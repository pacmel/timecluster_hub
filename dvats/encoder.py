# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/encoder.ipynb.

# %% auto 0
__all__ = ['ENCODER_EMBS_MODULE_NAME', 'get_gpu_memory_', 'color_for_percentage', 'create_bar', 'gpu_memory_status_',
           'DCAE_torch', 'get_enc_embs', 'get_enc_embs_set_stride_set_batch_size']

# %% ../nbs/encoder.ipynb 2
import subprocess
def get_gpu_memory_(device = 0):
    total_memory = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits", "--id=" + str(device)])
    total_memory = int(total_memory.decode().split('\n')[0])
    used_memory = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits",  "--id=" + str(device)])
    used_memory = int(used_memory.decode().split('\n')[0])

    percentage = round((used_memory / total_memory) * 100)
    return used_memory, total_memory, percentage

def color_for_percentage(percentage):
    if percentage < 20:
        return "\033[90m"  # Gray
    elif percentage < 40:
        return "\033[94m"  # Blue
    elif percentage < 60:
        return "\033[92m"  # Green
    elif percentage < 80:
        return "\033[93m"  # Orange
    else:
        return "\033[91m"  # Red
        
def create_bar(percentage, color_code, length=20):
    filled_length = int(length * percentage // 100)
    bar = "█" * filled_length + "-" * (length - filled_length)
    return color_code + bar + "\033[0m"  # Apply color and reset after bar

def gpu_memory_status_(device=0):
    used, total, percentage = get_gpu_memory_(device)
    color_code = color_for_percentage(percentage)
    bar = create_bar(percentage, color_code)
    print(f"GPU | Used mem: {used}")
    print(f"GPU | Used mem: {total}")
    print(f"GPU | Memory Usage: [{bar}] {color_code}{percentage}%\033[0m")


# %% ../nbs/encoder.ipynb 4
import pandas as pd
import numpy as np
from fastcore.all import *
from tsai.callback.MVP import *
from tsai.imports import *
from tsai.models.InceptionTimePlus import InceptionTimePlus
from tsai.models.explainability import get_acts_and_grads
from tsai.models.layers import *
from tsai.data.validation import combine_split_data
import time

# %% ../nbs/encoder.ipynb 7
class DCAE_torch(Module):
    def __init__(self, c_in, seq_len, delta, nfs=[64, 32, 12], kss=[10, 5, 5],
                 pool_szs=[2,2,3], output_fsz=10):
        """
        Create a Deep Convolutional Autoencoder for multivariate time series of `d` dimensions,
        sliced with a window size of `w`. The parameter `delta` sets the number of latent features that will be
        contained in the Dense layer of the network. The the number of features
        maps (filters), the filter size and the pool size can also be adjusted."
        """
        assert all_equal([len(x) for x in [nfs, kss, pool_szs]], np.repeat(len(nfs), 3)), \
            'nfs, kss, and pool_szs must have the same length'
        assert np.prod(pool_szs) == nfs[-1], \
            'The number of filters in the last conv layer must be equal to the product of pool sizes'
        assert seq_len % np.prod(pool_szs) == 0, \
            'The product of pool sizes must be a divisor of the window size'
        layers = []
        for i in range_of(kss):
            layers += [Conv1d(ni=nfs[i-1] if i>0 else c_in, nf=nfs[i], ks=kss[i]),
                       nn.MaxPool1d(kernel_size=pool_szs[i])]
        self.downsample = nn.Sequential(*layers)
        self.bottleneck = nn.Sequential(OrderedDict([
            ('flatten', nn.Flatten()),
            ('latent_in', nn.Linear(seq_len, delta)),
            ('latent_out', nn.Linear(delta, seq_len)),
            ('reshape', Reshape(nfs[-1], seq_len // np.prod(pool_szs)))
        ]))
        layers = []
        for i in reversed(range_of(kss)):
            layers += [Conv1d(ni=nfs[i+1] if i != (len(nfs)-1) else nfs[-1],
                              nf=nfs[i], ks=kss[i]),
                       nn.Upsample(scale_factor=pool_szs[i])]
        layers += [Conv1d(ni=nfs[0], nf=c_in, kernel_size=output_fsz)]
        self.upsample = nn.Sequential(*layers)


    def forward(self, x):
        x = self.downsample(x)
        x = self.bottleneck(x)
        x = self.upsample(x)
        return x

# %% ../nbs/encoder.ipynb 10
ENCODER_EMBS_MODULE_NAME = {
    InceptionTimePlus: 'backbone', # for mvp based models
    DCAE_torch: 'bottleneck.latent_in'
}

# %% ../nbs/encoder.ipynb 12
def get_enc_embs(X, enc_learn, module=None, cpu=False, average_seq_dim=True, to_numpy=True):
    """
        Get the embeddings of X from an encoder, passed in `enc_learn as a fastai
        learner. By default, the embeddings are obtained from the last layer
        before the model head, although any layer can be passed to `model`.
        Input
        - `cpu`: Whether to do the model inference in cpu of gpu (GPU recommended)
        - `average_seq_dim`: Whether to aggregate the embeddings in the sequence dimensions
        - `to_numpy`: Whether to return the result as a numpy array (if false returns a tensor)
    """
    print("--> Check CUDA")
    if cpu:
        print("--> Get enc embs CPU")
        enc_learn.dls.cpu()
        enc_learn.cpu()
    else:
        print("--> Ensure empty cache")
        torch.cuda.empty_cache()
        print("--> Use CUDA |Get enc embs GPU ")
        enc_learn.dls.cuda()
        enc_learn.cuda()
        if torch.cuda.is_available():
            print("CUDA está disponible")
            print("Dispositivo CUDA actual: ", torch.cuda.current_device())
            print("Nombre del dispositivo CUDA actual: ", torch.cuda.get_device_name(torch.cuda.current_device()))
            
        else:
            print("CUDA no está disponible ")
            print("Use CUDA -->")
    if enc_learn.dls.bs == 0: enc_learn.dls.bs = 64
    
    print("--> Set dataset from X (enc_learn does not contain dls)")
    aux_dl = enc_learn.dls.valid.new_dl(X=X)
    aux_dl.bs = enc_learn.dls.bs if enc_learn.dls.bs>0 else 64
    print("--> Get module")
    module = nested_attr(enc_learn.model,ENCODER_EMBS_MODULE_NAME[type(enc_learn.model)]) if module is None else module
    
    print("--> Get enc embs bs: ", aux_dl.bs)
    embs = [
        get_acts_and_grads(
            model=enc_learn.model,
            modules=module,
            x=xb[0], 
            cpu=cpu
        )[0] 
        for xb in aux_dl
    ]
    print("--> Concat")
    if not cpu:
        total_emb_size = sum([emb.element_size() * emb.nelement() for emb in embs])
        free_memory = torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated()
        if (total_emb_size < free_memory):
            print("Fit in GPU")
            embs=[emb.cuda() for emb in embs]
        else:
            print("Dont fit in GPU --> Go to CPU")
            embs=[emb.cpu() for emb in embs]
    embs = to_concat(embs)
    print("--> reduce")
    if embs.ndim == 3 and average_seq_dim: embs = embs.mean(axis=2)
    print("--> 2 numpy")
    if to_numpy: embs = embs.numpy() if cpu else embs.cpu().numpy()
    return embs

# %% ../nbs/encoder.ipynb 13
def get_enc_embs_set_stride_set_batch_size(
    X, enc_learn, stride, batch_size, module=None, cpu=False, average_seq_dim=True, to_numpy=True, 
    print_flag = False, time_flag=False, chunk_size = 0, check_memory_usage = False
):
    """
        Get the embeddings of X from an encoder, passed in `enc_learn as a fastai
        learner. By default, the embeddings are obtained from the last layer
        before the model head, although any layer can be passed to `model`.
        Input
        - `cpu`: Whether to do the model inference in cpu of gpu (GPU recommended)
        - `average_seq_dim`: Whether to aggregate the embeddings in the sequence dimensions
        - `to_numpy`: Whether to return the result as a numpy array (if false returns a tensor)
    """
    if time_flag:
        t_start = time.time()
    if print_flag:
        print("--> get_enc_embs_set_stride_set_batch_size")
    if check_memory_usage: gpu_memory_status_()
        #print("get_enc_embs_set_stride_set_batch_size | Check versions")
        #import sys
        #print("get_enc_embs_set_stride_set_batch_size | Check versions | Python version", sys.version)
        #print("get_enc_embs_set_stride_set_batch_size | Check versions | PyTorch version", torch.__version__)
        #print("get_enc_embs_set_stride_set_batch_size | Check versions | CUDA version", torch.version.cuda)
        #print("get_enc_embs_set_stride_set_batch_size | Apply stride & batch size")
    
    X = X[::stride]
    enc_learn.dls.bs = batch_size 
    
    if (print_flag): print("get_enc_embs_set_stride_set_batch_size | Check CUDA | X ~ ", X.shape[0])
    if cpu:
        if (print_flag): print("get_enc_embs_set_stride_set_batch_size | Get enc embs CPU")
        enc_learn.dls.cpu()
        enc_learn.cpu()
    else:
        if torch.cuda.is_available():
            if (print_flag): 
                print("get_enc_embs_set_stride_set_batch_size | CUDA device id:", torch.cuda.current_device())
                print("get_enc_embs_set_stride_set_batch_size | CUDA device name: ", torch.cuda.get_device_name(torch.cuda.current_device()))
                print("get_enc_embs_set_stride_set_batch_size | Ensure empty cache & move 2 GPU")
            torch.cuda.empty_cache()
            enc_learn.dls.cuda()
            enc_learn.cuda()
        else:
            if (print_flag): print("get_enc_embs_set_stride_set_batch_size | No cuda available. Set CPU = true")
            cpu = True
    
    if enc_learn.dls.bs == 0: enc_learn.dls.bs = 64

    if (print_flag): print("get_enc_embs_set_stride_set_batch_size | Set dataset from X (enc_learn does not contain dls)")
    aux_dl = enc_learn.dls.valid.new_dl(X=X)
    aux_dl.bs = enc_learn.dls.bs if enc_learn.dls.bs>0 else 64
    if (print_flag): print("get_enc_embs_set_stride_set_batch_size | Get module")
    module = nested_attr(enc_learn.model,ENCODER_EMBS_MODULE_NAME[type(enc_learn.model)]) if module is None else module
    
    if (print_flag): 
        #print("get_enc_embs_set_stride_set_batch_size | Get acts and grads | module ", module)
        print("get_enc_embs_set_stride_set_batch_size | Get acts and grads | aux_dl len", len(aux_dl))
        print("get_enc_embs_set_stride_set_batch_size | Get acts and grads | aux_dl.batch_len ", len(next(iter(aux_dl))))
        print("get_enc_embs_set_stride_set_batch_size | Get acts and grads | aux_dl.bs ", aux_dl.bs)
        if (not cpu):
            total = torch.cuda.get_device_properties(device).total_memory
            used = torch.cuda.memory_allocated(torch.cuda.current_device())
            reserved = torch.cuda.memory_reserved(torch.cuda.current_device())
            print("get_enc_embs_set_stride_set_batch_size | Get acts and grads | total_mem ", total)
            print("get_enc_embs_set_stride_set_batch_size | Get acts and grads | used_mem ", used)
            print("get_enc_embs_set_stride_set_batch_size | Get acts and grads | reserved_mem ", reserved)
            print("get_enc_embs_set_stride_set_batch_size | Get acts and grads | available_mem ", total-reserved)
            sys.stdout.flush()
                                              
    if (cpu or ( chunk_size == 0 )):
        embs = [
            get_acts_and_grads(
                model=enc_learn.model,
                modules=module, 
                x=xb[0], 
                cpu=cpu
            )[0] 
            for xb in aux_dl
        ]
        if not cpu: embs=[emb.cpu() for emb in embs]
    else:
        embs = []
        total_chunks=max(1,round(len(X)/chunk_size))
        if print_flag: print("get_enc_embs_set_stride_set_batch_size | Get acts and grads | aux_dl len | " + str(len(X)) + " chunk size: " + str(chunk_size) + " => " + str(total_chunks) + " chunks")
        for i in range(0, total_chunks):
            if print_flag: 
                print("get_enc_embs_set_stride_set_batch_size | Get acts and grads | Chunk [ " + str(i) + "/"+str(total_chunks)+"] => " + str(round(i*100/total_chunks)) + "%")
                sys.stdout.flush()
            chunk = [batch for (n, batch) in enumerate(aux_dl) if (chunk_size*i <= n  and chunk_size*(i+1) > n) ]
            chunk_embs = [
                get_acts_and_grads(
                    model=enc_learn.model,
                    modules=module,
                    x=xb[0], 
                    cpu=cpu
                )[0]
                for xb in chunk
            ]
            # Mueve los embeddings del bloque a la CPU
            chunk_embs = [emb.cpu() for emb in chunk_embs]
            embs.extend(chunk_embs)
            torch.cuda.empty_cache()
        if print_flag: 
            print("get_enc_embs_set_stride_set_batch_size | Get acts and grads | 100%")
            sys.stdout.flush()
    
    if print_flag: print("get_enc_embs_set_stride_set_batch_size | concat embeddings")
    
    embs = to_concat(embs)
    
    if print_flag: print("get_enc_embs_set_stride_set_batch_size | Reduce")
    
    if embs.ndim == 3 and average_seq_dim: embs = embs.mean(axis=2)
    
    if print_flag: print("get_enc_embs_set_stride_set_batch_size | Convert to numpy")
    
    if to_numpy: 
        if cpu or chunk_size > 0:
            embs = embs.numpy() 
        else: 
            embs = embs.cpu().numpy()
            torch.cuda.empty_cache()
    if time_flag:
        t = time.time()-t_start
        if print_flag:
            print("get_enc_embs_set_stride_set_batch_size " + str(t) + " seconds -->")
        else:
            print("get_enc_embs_set_stride_set_batch_size " + str(t) + " seconds")
    if check_memory_usage: gpu_memory_status_()
    if print_flag: 
        print("get_enc_embs_set_stride_set_batch_size -->")
    return embs
