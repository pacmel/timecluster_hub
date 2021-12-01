#FROM ubuntu:20.04
FROM nvidia/cuda:11.2.1-cudnn8-runtime-ubuntu20.04

LABEL maintainer="vrodriguezf <victor.rfernandez@upm.es>"

SHELL [ "/bin/bash", "--login", "-c" ]

RUN apt-get update --fix-missing && \
    apt-get install -y wget bzip2 curl git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Environmental variables for wandb
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Create a non-root user
ARG username=user
ARG uid=1000
ARG gid=1000
ENV USER $username
ENV UID $uid
ENV GID $gid
ENV HOME /home/$USER

RUN addgroup --gid $GID $USER

RUN adduser --disabled-password \
    --gecos "Non-root user" \
    --uid $UID \
    --gid $GID \
    --home $HOME \
    $USER

USER $USER

# Add the jupyterlab settings
COPY --chown=$uid:$gid docker/jupyter_config $HOME/.jupyter

# install miniconda
ENV MINICONDA_VERSION 4.10.3
ENV CONDA_DIR $HOME/miniconda3
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-py38_$MINICONDA_VERSION-Linux-x86_64.sh -O ~/miniconda.sh && \
    chmod +x ~/miniconda.sh && \
    ~/miniconda.sh -b -p $CONDA_DIR && \
    rm ~/miniconda.sh

# make non-activate conda commands available
ENV PATH=$CONDA_DIR/bin:$PATH

# make conda activate command available from /bin/bash --login shells
RUN echo ". $CONDA_DIR/etc/profile.d/conda.sh" >> ~/.profile

# make conda activate command available from /bin/bash --interative shells
RUN conda init bash

# create a project directory inside user home
ENV PROJECT_DIR $HOME
RUN mkdir -p $PROJECT_DIR
WORKDIR $PROJECT_DIR

# Install and update mamba
ENV ENV_PREFIX $PROJECT_DIR/env
RUN conda install --name base --channel conda-forge mamba
RUN mamba update --name base --channel defaults conda

# build the mamba environment
COPY --chown=$UID:$GID docker/environment.yml docker/requirements.txt /tmp/
RUN mamba env create --prefix $ENV_PREFIX --file /tmp/environment.yml --force
RUN conda clean --all --yes

# run the postBuild script to install the JupyterLab extensions
COPY --chown=$UID:$GID docker/postBuild /usr/local/bin
RUN chmod u+x /usr/local/bin/postBuild
RUN conda activate $ENV_PREFIX && \
    /usr/local/bin/postBuild && \
    conda deactivate

# Make bash automatically activate the conda environment
RUN echo "conda activate $ENV_PREFIX" >> ~/.bashrc

# Ipython config
#COPY --chown=$UID:$GID ./ipython_config.py $HOME

# Reinstall pytorch (fix for gtx 3090)
RUN conda activate $ENV_PREFIX && \
    pip install torch==1.7.1+cu110 torchvision==0.8.2+cu110 -f https://download.pytorch.org/whl/torch_stable.html && \
    conda deactivate

# Editable packages (pip)
RUN mkdir /home/$USER/lib
RUN conda activate $ENV_PREFIX && \
    cd /home/$USER/lib \
    && git clone https://github.com/timeseriesAI/tsai.git \
    && cd tsai \ 
    && pip install -e . && \
    conda deactivate

# Fix protobuf mismatch after tsai installation
RUN conda activate $ENV_PREFIX && \
    pip install protobuf==3.18.1 && \  
    conda deactivate

# use an entrypoint script to insure conda environment is properly activated at runtime
COPY --chown=$UID:$GID docker/entrypoint.sh /usr/local/bin
RUN chmod u+x /usr/local/bin/entrypoint.sh
ENTRYPOINT [ "/usr/local/bin/entrypoint.sh" ]

# default command will be to launch JupyterLab server for development
CMD [ "jupyter", "lab", "--no-browser", "--ip", "0.0.0.0", "--ContentsManager.allow_hidden=True"]
