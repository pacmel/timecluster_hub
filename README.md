# Deep VATS
> Deep learning Visual Analytics for Time Series

The main objective of DeepVATS is to combine cutting-edge research in neural networks and visual analytics of time series. It is inspired by projects such as [Timecluster](https://link.springer.com/article/10.1007/s00371-019-01673-y) and the [TensorFlow's Embeddings Projector](https://projector.tensorflow.org/), in which tools are created to interpret the content of neural networks trained with visual and textual data. This allows to verify how the internal content of a neural network reveals high-level abstraction patterns present in the data (for example, semantic similarity between words in a language model).

![General scheme of DeepVATS. Visualizing the embeddings can help in easily detecting outliers, change points, and regimes.
](https://github.com/vrodriguezf/deepvats/blob/master/imgs/deepvats_intro.png)

Given a set of time series data, DeepVATS will allow three basic tasks to be carried out:
1. Train neural networks to search for representations that contain, in a compressed way, meaningful patterns of that data.
2. Project and visualize the content of the latent space of neural network in a way that allows the search for patterns and anomalies.
3. Provide interactive visualizations to explore different perspectives of the latent space.

Currently, DeepVATS is recommended for time series data with the following properties:
- Univariate & Multivariate time series
- With or without natural timesteps
- Regular timestamps
- 1 single series at a time
- Suitable for long time series that present cyclical patterns

## Structure

The tool consists of three modules. The DL (Deep Learning) module sets the pipeline for training the 'backbone' neural netowirk model. The second module, namely the storage module, provides an API that allows to save the datatsets and de encoder models produced by the DL module, and load the into the Visual Analytics module to be used for inference. That module, the VA (Visual Analytics) module, allows to use the trained models in a exploratory way throught a Graphical User Interface (GUI). 

![DeepVATS architecture](https://github.com/vrodriguezf/deepvats/blob/master/imgs/architecture.png)

## How it works

The tool can be used for different time series data mining tasks, such as segmentation or detection of repetitive patterns (motifs) and anomalies (outliers). This example shows the use of the tool with a pre-trained model for segmentation.

![Using the DeepVATS GUI](https://github.com/vrodriguezf/deepvats/blob/master/imgs/deepvats.gif)

## Deploy

To run the notebooks and the app, install `docker`, `docker-compose` and the [nvidia container toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) in your system. 
> Note: Your system needs an NVIDIA GPU

Then, create a new *.env* file inside the folder `docker` of the project adding the following config variables liste below.

> Note: You need to have an account in [Weights & Biases (wandb)](https://wandb.ai/).

```
# The name of the docker-compose project
COMPOSE_PROJECT_NAME=your_project_name
# The user ID you are using to run docker-compose
USER_ID=your_numeric_id
# The group ID you are using to run docker-compose (you can get it with id -g in a terminal)
GROUP_ID=your_numeric_id
# The user name assigned to the user id
USER_NAME=your_user_name
# The port from which you want to access Jupyter lab
JUPYTER_PORT=
# The token used to access (like a password)
JUPYTER_TOKEN=
# The path to your data files to train/test the models
LOCAL_DATA_PATH=/path/to/your/data
# The W&B entity
WANDB_ENTITY=
# The W&B project
WANDB_PROJECT=
# The W&B personal API key (see https://wandb.ai/authorize)
WANDB_API_KEY=your_wandb_api_key
# List of comma separated GPU indices that will be available in the container (by default only 0, the first one)
CUDA_VISIBLE_DEVICES=0
# Github PAT (see https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and>
GH_TOKEN=your_github_pat
# Port in which you want Rstudio server to be deployed (for developing in the front end)
RSTUDIO_PORT=
# Password to access the Rstudio server
RSTUDIO_PASSWD=
```

Alternatively, you can run ./docker/env.sh so the file .env is automatically generated with the basic user data to ensure the proper build of dockers.


Finally, in a terminal located in the folder `docker` of this repository, run:

```docker-compose up -d```

then go to `localhost:{{JUPYTER_PORT}}` to run/edit the notebooks (backend) or go to `localhost:{{RSTUDIO_PORT}}` to edit the visualization module (frontend). 

> Note: In case you are working in a remote server, replace `localhost` with the IP of your remote server.

To run the GUI, enter the visualization service in `localhost:{{RSTUDIO_PORT}}`, 
and then run, in the R console: 
```r
shiny::runApp("app")
```


## Contribute to the backend

The backend of the project has been created using [nbdev](https://github.com/fastai/nbdev), a library that allows to create Python projects directly from Jupyter Notebooks. Please refer to this library when adding new functionalities to the project, in order to keep the structure of it.

We recommend using the following procedure to contribute and resolve issues in the repository:

1. Because the project uses nbdev, we need to run `nbdev_install_git_hooks` the first time after the repo is cloned and deployed; this ensures that our notebooks are automatically cleaned and trusted whenever we push to Github/Gitlab. The command has to be run from within the container. Also, it can be run from outside if you pip install nbdev in your local machine.

1. Create a local branch in your development environment to solve the issue XX (or add a new functionality), with the name you want to give your merge request (use something that will be easy for you to remember in the future if you need to update your request):
    ```
    git checkout -b issueXX
    ```

2. Make whatever changes you want to make in the code and notebooks, and remember to run nbdev_build_lib when you're done to ensure that the libraries are built from your notebook changes (unless you only changed markdown, in which case that's not needed). It's also a good idea to check the output of git diff to ensure that you haven't accidentally made more changes than you planned.

3. Make a commit of the changes made
    ``` 
    git commit -am "Fix issue #XX"
    ```

4. Test that there are not merging problems in the Jupyter Notebooks with the function [**nbdev_fix_merge**](https://nbdev.fast.ai/cli#nbdev_fix_merge)

5.  Push your local branch to a branch in the gitlab repository with an identiffying name:
    ```
    git push -u origin HEAD
    ```
6. When the push is made, a link will appear in the terminal to create a merge request. Click on it.
    ```
    remote:
    remote: To create a merge request for test_branch, visit:
    remote:   https://gitlab.geist.re/pml/x_timecluster_extension/-/merge_requests/new?merge_request%5Bsource_branch%5D=issueXX_solved
    remote:
    ```
7. In the gitlab website:
    * Write in the description what is the problem to solve with your branch using a hyperlink to the issue (just use the hashtag symbol "#" followed by the issue number) 
    * Click on the option "Delete source branch when merge request is accepted" and assign the merge to your profile.
    * Click on the button "Create merge request"
![image](../../../uploads/da18a985a69973ad62a60bc6564304b9/image.png)

8. Wait to the merge to be accepted. In case you're solving an issue, we recommend to move the issue to the field "In review" (in the Issue Board). To keep your branch up to date with the changes to the main repo, run:
```
git pull upstream master
```

9. If there are no problems, the merge request will be accepted and the issue will be closed. Once your PR has been merged or rejected, you can delete your branch if you don't need it any more:
```
git branch -d issueXX
```

## Cite

If you use DeepVATS, please cite the paper:

``` text
@article{RODRIGUEZFERNANDEZ2023110793,
title = {DeepVATS: Deep Visual Analytics for Time Series},
journal = {Knowledge-Based Systems},
volume = {277},
pages = {110793},
year = {2023},
issn = {0950-7051},
doi = {https://doi.org/10.1016/j.knosys.2023.110793},
author = {Victor Rodriguez-Fernandez and David Montalvo-Garcia and Francesco Piccialli and Grzegorz J. Nalepa and David Camacho}
}
```
