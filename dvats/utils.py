# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/utils.ipynb.

# %% auto 0
__all__ = ['generate_TS_df', 'normalize_columns', 'remove_constant_columns', 'ReferenceArtifact', 'PrintLayer',
           'get_wandb_artifacts', 'get_pickle_artifact', 'exec_with_feather', 'py_function',
           'exec_with_feather_k_output', 'exec_with_and_feather_k_output', 'Time', 'funcname', 'update_patch',
           'styled_print', 'show_sequence', 'plot_with_dots', 'Interpolator', 'PAATransformer', 'DownsampleError',
           'DivisorsError', 'divisors', 'downsample_propose_crop_', 'downsample', 'print_flush',
           'find_dominant_window_sizes_list_single_old', 'select_separated_sizes',
           'find_dominant_window_sizes_list_single', 'group_similar_sizes', 'find_dominant_window_sizes_list']

# %% ../nbs/utils.ipynb 3
from .imports import *
from fastcore.all import *
import wandb
import pickle
import pandas as pd
import numpy as np
#import tensorflow as tf
import torch.nn as nn
from fastai.basics import *

# %% ../nbs/utils.ipynb 5
def generate_TS_df(rows, cols):
    "Generates a dataframe containing a multivariate time series, where each column \
    represents a variable and each row a time point (sample). The timestamp is in the \
    index of the dataframe, and it is created with a even space of 1 second between samples"
    index = np.arange(pd.Timestamp.now(),
                      pd.Timestamp.now() + pd.Timedelta(rows-1, 'seconds'),
                      pd.Timedelta(1, 'seconds'))
    data = np.random.randn(len(index), cols)
    return pd.DataFrame(data, index=index)

# %% ../nbs/utils.ipynb 10
def normalize_columns(df:pd.DataFrame):
    "Normalize columns from `df` to have 0 mean and 1 standard deviation"
    mean = df.mean()
    std = df.std() + 1e-7
    return (df-mean)/std

# %% ../nbs/utils.ipynb 16
def remove_constant_columns(df:pd.DataFrame):
    return df.loc[:, (df != df.iloc[0]).any()]

# %% ../nbs/utils.ipynb 21
class ReferenceArtifact(wandb.Artifact):
    default_storage_path = Path('data/wandb_artifacts/') # * this path is relative to Path.home()
    "This class is meant to create an artifact with a single reference to an object \
    passed as argument in the contructor. The object will be pickled, hashed and stored \
    in a specified folder."
    @delegates(wandb.Artifact.__init__)
    def __init__(self, obj, name, type='object', folder=None, **kwargs):
        super().__init__(type=type, name=name, **kwargs)
        # pickle dumps the object and then hash it
        hash_code = str(hash(pickle.dumps(obj)))
        folder = Path(ifnone(folder, Path.home()/self.default_storage_path))
        with open(f'{folder}/{hash_code}', 'wb') as f:
            pickle.dump(obj, f)
        self.add_reference(f'file://{folder}/{hash_code}')
        if self.metadata is None:
            self.metadata = dict()
        self.metadata['ref'] = dict()
        self.metadata['ref']['hash'] = hash_code
        self.metadata['ref']['type'] = str(obj.__class__)

# %% ../nbs/utils.ipynb 24
@patch
def to_obj(self:wandb.apis.public.Artifact):
    """Download the files of a saved ReferenceArtifact and get the referenced object. The artifact must \
    come from a call to `run.use_artifact` with a proper wandb run."""
    if self.metadata.get('ref') is None:
        print(f'ERROR:{self} does not come from a saved ReferenceArtifact')
        return None
    original_path = ReferenceArtifact.default_storage_path/self.metadata['ref']['hash']
    path = original_path if original_path.exists() else Path(self.download()).ls()[0]
    with open(path, 'rb') as f:
        obj = pickle.load(f)
    return obj

# %% ../nbs/utils.ipynb 33
import torch.nn as nn
class PrintLayer(nn.Module):
    def __init__(self):
        super(PrintLayer, self).__init__()

    def forward(self, x):
        # Do your print / debug stuff here
        print(x.shape)
        return x

# %% ../nbs/utils.ipynb 34
@patch
def export_and_get(self:Learner, keep_exported_file=False):
    """
        Export the learner into an auxiliary file, load it and return it back.
    """
    aux_path = Path('aux.pkl')
    self.export(fname='aux.pkl')
    aux_learn = load_learner('aux.pkl')
    if not keep_exported_file: aux_path.unlink()
    return aux_learn

# %% ../nbs/utils.ipynb 36
def get_wandb_artifacts(project_path, type=None, name=None, last_version=True):
    """
        Get the artifacts logged in a wandb project.
        Input:
        - `project_path` (str): entity/project_name
        - `type` (str): whether to return only one type of artifacts
        - `name` (str): Leave none to have all artifact names
        - `last_version`: whether to return only the last version of each artifact or not

        Output: List of artifacts
    """
    public_api = wandb.Api()
    if type is not None:
        types = [public_api.artifact_type(type, project_path)]
    else:
        types = public_api.artifact_types(project_path)

    res = L()
    for kind in types:
        for collection in kind.collections():
            if name is None or name == collection.name:
                versions = public_api.artifact_versions(
                    kind.type,
                    "/".join([kind.entity, kind.project, collection.name]),
                    per_page=1,
                )
                if last_version: res += next(versions)
                else: res += L(versions)
    return list(res)

# %% ../nbs/utils.ipynb 39
def get_pickle_artifact(filename):

    with open(filename, "rb") as f:
        df = pickle.load(f)
    
    return df

# %% ../nbs/utils.ipynb 41
import pyarrow.feather as ft
import pickle

# %% ../nbs/utils.ipynb 42
def exec_with_feather(function, path = None, verbose = 0, *args, **kwargs):
    result = None
    if not (path is None):
        if verbose > 0: print("--> Exec with feather | reading input from ", path)
        input = ft.read_feather(path)
        if verbose > 0: print("--> Exec with feather | Apply function ", path)
        result = function(input, *args, **kwargs)
        if verbose > 0: print("Exec with feather --> ", path)
    return result

# %% ../nbs/utils.ipynb 43
def py_function(module_name, function_name, verbose = 0):
    try:
        function = getattr(__import__('__main__'), function_name)
    except:
        module = __import__(module_name, fromlist=[''])
        function = getattr(module, function_name)
    print("py function: ", function_name, ": ", function)
    return function

# %% ../nbs/utils.ipynb 46
import time
def exec_with_feather_k_output(function_name, module_name = "main", path = None, k_output = 0, verbose = 0, time_flag = False, *args, **kwargs):
    result = None
    function = py_function(module_name, function_name,verbose)
    if time_flag: t_start = time.time()
    if not (path is None):
        if verbose > 0: print("--> Exec with feather | reading input from ", path)
        input = ft.read_feather(path)
        if verbose > 0: print("--> Exec with feather | Apply function ", path)
        result = function(input, *args, **kwargs)[k_output]
    if time_flag:
        t_end = time.time()
        print("Exec with feather | time: ", t_end-t_start)
    if verbose > 0: print("Exec with feather --> ", path)
    return result

# %% ../nbs/utils.ipynb 48
def exec_with_and_feather_k_output(function_name, module_name = "main", path_input = None, path_output = None, k_output = 0, verbose = 0, time_flag = False, *args, **kwargs):
    result = None
    function = py_function(module_name, function_name, verbose-1)
    if time_flag: t_start = time.time()
    if not (path_input is None):
        if verbose > 0: print("--> Exec with feather | reading input from ", path_input)
        input = ft.read_feather(path_input)
        if verbose > 0: 
            print("--> Exec with feather | Apply function ", function_name, "input type: ", type(input))
        
        result = function(input, *args, **kwargs)[k_output]
        ft.write_feather(df, path, compression = 'lz4')
    if time_flag:
        t_end = time.time()
        print("Exec with feather | time: ", t_end-t_start)
    if verbose > 0: print("Exec with feather --> ", path_output)
    return path_output

# %% ../nbs/utils.ipynb 50
import time
from dataclasses import dataclass, field

# %% ../nbs/utils.ipynb 51
@dataclass
class Time:
    time_start  : float =  None
    time_end    : float =  None
    time_total  : float =  0.0
    function    : str   =  ''

    def start(self, verbose = 0): 
        if verbose > 0: print("--> Start: ", self.function)
        self.time_start = time.time()
        return self.time_start

    def end(self, verbose= 0):
        self.time_end = time.time()
        self.time_total = self.duration()
        if verbose > 0: print("End: ", self.function, "-->")
        return self.time_end
        
    def duration(self):
        self.time_total=self.time_end - self.time_start
        return self.time_total
    def show(self):
        if self.time_start is None: 
            print(f"[{self.function}] Not started")
        elif self.time_end is None:
            print(f"[{self.function}] Not ended | Start: ", self.time_start)
        else:
            print(f"[{self.function}] Start: {self.time_start} | End: {self.time_end} | Duration: {self.time_total} seconds")
        return self.time_total     

# %% ../nbs/utils.ipynb 52
def funcname():
    """Get calling function name"""
    return inspect.stack()[1][3]

# %% ../nbs/utils.ipynb 55
#Function for making notebooks clearer
from IPython.display import clear_output, DisplayHandle
def update_patch(self, obj):
    clear_output(wait=True)
    self.display(obj)
    print("... Enabling Vs Code execution ...")

# %% ../nbs/utils.ipynb 58
from IPython.display import display, HTML

# %% ../nbs/utils.ipynb 59
def styled_print(text, color='black', size='16px', weight='normal'):
    html_text = f"<span style='color: {color}; font-size: {size}; font-weight: {weight};'>{text}</span>"
    display(HTML(html_text))

# %% ../nbs/utils.ipynb 62
def show_sequence(
    data         : List[ List [ float ] ] = None, 
    hide_rows    : bool = False, 
    hide_columns : bool = True
):
    """
    Show the sequence in a nice format similar to stumpy tutorials
    """
    df          = pd.DataFrame(data)
    styled_df   = df.style
    if hide_rows: 
        styled_df = styled_df.hide(axis='index')
    if hide_columns: 
        styled_df = styled_df.hide(axis='columns')
    styled_df = styled_df.set_table_styles([
        {'selector': '',
         'props': [('border', '2px solid black'),
                   ('text-align', 'center'),
                   ('font-family', 'Arial'),
                   ('border-collapse', 'collapse')]},
        {'selector': 'td',
         'props': [('border', '1px solid black'),
                   ('padding', '5px')]}
    ])
    display(styled_df)

# %% ../nbs/utils.ipynb 63
def plot_with_dots(
    time_series             : List[float]    = None,
    xlabel                  : str            = 'Index (time)',
    ylabel                  : str            = 'Value',
    title                   : str            = 'Time series',
    sequence_flag           : bool           = True,
    show_sequence_before    : bool           = True, 
    hide_rows               : bool           = True,
    hide_columns            : bool           = False,
    show_title              : bool           = True,
    fontsize                : int            = 10,
    save_plot               : bool           = False,
    dots                    : bool           = True,
    figsize                 : Tuple[int, int]= (10, 6),
    plot_path               : str            = "./",
    plot_name               : str            = ""
  ) -> None:
    if sequence_flag and show_sequence_before: 
        show_sequence([time_series], hide_rows, hide_columns)
    n = len(time_series)
    x_coords = range(n)
    
    plt.figure(figsize=figsize)  # Crear la figura con el tamaño especificado
    
    if dots: 
        plt.plot(x_coords, time_series)
        plt.scatter(x_coords, time_series, color='red')
    else:
        plt.plot(x_coords, time_series, linestyle='-')
        
    if show_title: 
        plt.title(title, fontsize=fontsize)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if save_plot:
        plot_path = os.path.expanduser(plot_path)
        if plot_name == "":
            plot_name = title
        plot_path = os.path.join(plot_path, plot_name + ".png")
        plt.savefig(plot_path)
    plt.show()
    if sequence_flag and not show_sequence_before:
        show_sequence([time_series], hide_rows, hide_columns)
    return None


# %% ../nbs/utils.ipynb 67
## -- Classes & types
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Callable

# %% ../nbs/utils.ipynb 68
from sklearn.base import TransformerMixin, BaseEstimator
from sklearn.pipeline import Pipeline

# %% ../nbs/utils.ipynb 69
@dataclass
class Interpolator(BaseEstimator, TransformerMixin):
    method            : str  ='linear'
    n_segments        : int  = 1
    plot_original_data: bool = False
    plot_interpolated : bool = False
    verbose           : int  = 0
    
    def fit(self, X, y=None):
        return self

    def transform(self, X):
                
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        if self.plot_original_data:
            if self.verbose > 0: print("Interpolator | Plot original data")
            for dim in range (X.ndim-1):
                if self.verbose > 1: print(f"Interpolator | Plot original data dimension {dim}")
                plot_with_dots(
                    X[dim], 
                    sequence_flag = False, 
                    title = f'Original data | dim {dim}'
                )
                
        n_samples, n_features = X.shape
        if n_features % self.n_segments != 0 or n_features == self.n_segments:
            raise ValueError(
                f"The number of segments {self.n_segments} must divide (and be different of) the number of features {n_features} | Reminder: {n_features // self.n_segments}"
            )

        segment_size = n_features // self.n_segments
        interpolated_result = np.full_like(X, np.nan)

        if self.verbose > 0: print(f"NFeatures: {n_features} | NSegments: {self.n_segments} | segment_size: {segment_size} | interpolated result ~ {interpolated_result.shape}")
        
        for i in np.arange(self.n_segments):
            start = i * segment_size 
            end = start + segment_size
            segment_mean = np.nanmean(X[:, start:end], axis=1)
            for j in np.arange(n_samples):
                nan_mask = np.isnan(X[j, start:end])
                interpolated_result[j, start:end][nan_mask] = segment_mean[j]
        res = np.where(np.isnan(X), interpolated_result, X)
        if self.plot_interpolated:
            for dim in range (X.ndim-1):
                plot_with_dots(
                    res[dim], 
                    sequence_flag = False, 
                    title = f'Interpolated data | dim {dim}'
                )
            
        return res

# %% ../nbs/utils.ipynb 71
@dataclass
class PAATransformer(BaseEstimator, TransformerMixin):
    n_segments       : int  = 1
    plot_aggregated  : bool = True
    verbose          : int  = 0

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        n_samples, n_features = X.shape
        if n_features <= self.n_segments:
            raise ValueError(f"The number of segments ({self.n_segments}) must be lower than the number of points ({n_features})")

        segment_size = n_features // ( self.n_segments + 1)
        remainder = n_features % ( self.n_segments + 1)

        if self.verbose > 0: 
            print(f"NFeatures: {n_features} | NSegments: {self.n_segments} | Segment size: {segment_size} | Reminder: {remainder}")

        # Crear un array para los resultados
        result = np.zeros((n_samples, self.n_segments + 1))

        if self.verbose > 1: print(f"Result ~ {result.shape}")

        # Procesar cada segmento
        for i in range(self.n_segments+1):
            start = i * segment_size + min(i, remainder)
            end = start + segment_size + (1 if i < remainder else 0)
            result[:, i] = np.mean(X[:, start:end], axis=1)

        if self.plot_aggregated:
            for dim in range (X.ndim-1):
                if self.verbose > 1:
                    print("Plos res | Dim", dim)
                plot_with_dots(
                    result[dim], 
                    sequence_flag = False, 
                    title = f'Aggregated data | dim {dim}',
                    fontsize = 20,
                    save_plot = True
                )

        return result


# %% ../nbs/utils.ipynb 73
# Errors definitions
class DownsampleError(Exception):
    """Exception raised for errors in the downsample process."""
    def __init__(self, message="Invalid number of min/max points for the proposed time series. You must allow cropping and check the final length"):
        self.message = message
        super().__init__(self.message)
class DivisorsError(Exception):
    def __init__(self, message = "Invalid parameters"):
        self.message = message
        super().__init__(self.message)

# %% ../nbs/utils.ipynb 74
def divisors(
    N : int, 
    min_val:int, 
    max_val:int, 
    verbose = 0
) -> List [ int ] : 
    print("Verbose: ", verbose)
    if verbose > 0: 
        print(f"Looking for the divisors of {N} between {min_val} and {max_val}")
    if (N < 0 or min_val < 0):
        mssg = f"N, min_val, max_val {N}, {min_val}, {max_val} must be a positive integer (>0)"
        raise DivisorsError(mssg)
    elif ( min_val > max_val):
        mssg = f"min_val > max_val ({min_val} > {max_val}). Please take a look"
        raise DivisorsError(mssg)
    arr = np.arange(min_val,max_val+1)
    arr = arr[ N % arr == 0]
    if verbose > 0: print(f"Found {len(arr)} divisors of {N} between {min_val} and {max_val}")
    return arr

def downsample_propose_crop_(
    N            : int, 
    min_points   : int, 
    max_points   : int, 
    verbose      : int  = 0,
    allow_crop   : bool = True,
    nearest_val  : bool = False,
    potential_val: int = 1
) -> int:
    if verbose > 0: 
        print(f"Verbose: {verbose}")
        print(f"Downsample Propose Crop | Prev N: {N}")
    all_divisors = divisors(
        N       = N, 
        min_val = min_points, 
        max_val = max_points,
        verbose = verbose-1
    )
    val = 0
    if len(all_divisors) == 0:
        if ( not nearest_val or potential_val < 1):
            raise ValueError("No valid divisors found for the given N within the min and max points range.")
    else:
        if ( nearest_val and potential_val > 0):
                val = min(all_divisors, key=lambda x: abs(x - potential_val))
        elif (divisors_flag):
            val = divisors(
                N       = N, 
                min_val = min_points, 
                max_val = max_points, 
                verbose = verbose-1
            )[-1]
    
    if (allow_crop):
        while (val < min_points and N > min_points): 
            N = N-1
            all_divisors = divisors(
                N       = N, 
                min_val = min_points, 
                max_val = max_points, 
                verbose = verbose-1
            )
            if len(all_divisors) > 0:
                if ( nearest_val and potential_val > 0):
                    val = min(all_divisors, key=lambda x: abs(x - potential_val))
    else: 
        raise DownsampleError()
        return -1
    if verbose > 0: print(f"Downsample Propose Crop | Post N: {N} | Largest Divisor: {val}")
    return (val, N)

# %% ../nbs/utils.ipynb 76
def downsample(
    data  : List [ float ] = None,
    min_position : int  = 0,
    max_position : int  = -1, 
    min_points   : int  = 1,
    max_points   : int  = 10000,
    verbose      : int  = 1,
    show_plots   : bool = False,
    allow_crop   : bool = True
) -> Tuple [ List [ float ], float ]:  
    if max_points >= data.shape[0]: return data, 1
    if verbose > 1: print(f"[ Downsample | Position ] Before | Pos ({min_position}, {max_position})")
    min_position = min_position if min_position > 0 else 0
    max_position = max_position if ( max_position > -1 and max_position < data.shape[0]) else data.shape[0]
    if verbose > 1: print(f"[ Downsample | Position ] After | Pos ({min_position}, {max_position})")
    
    n_timestamps = max_position - min_position
    paa_factor   = np.maximum(1, n_timestamps // max_points)

    min_points   = max(1,min(min_points, data.shape[0]))
    max_points   = min(data.shape[0], min(max_points, max_position-min_position))

    if verbose > 1:
        print(f"[ Downsample | downsample_propose_crop ] Max points: {max_points}")
        print(f"[ Downsample | downsample_propose_crop ] Min points: {min_points}")
    
    
    min_points   = min(min_points, max_points)
    
    if verbose > 1:
        print(f"[ Downsample | downsample_propose_crop ] N timestamps {n_timestamps}")
        print(f"[ Downsample | downsample_propose_crop ] PAA factor: {paa_factor}")
        
        print(f"[ Downsample | downsample_propose_crop ] allow_crop: {allow_crop}")

    potential_segments = np.floor(n_timestamps / paa_factor).astype(int)
    
    N = max_position-min_position
    
    if verbose > 1:
        print(f"[ Downsample | downsample_propose_crop ] N: {N}")
        print(f"[ Downsample | downsample_propose_crop ] potential_segments: {potential_segments}")
        
    n_segments, N = downsample_propose_crop_(
        N             = N, 
        min_points    = min_points,
        max_points    = max_points,
        verbose       = verbose-1,
        allow_crop    = allow_crop,
        nearest_val   = allow_crop, # If allow_crop, try to get as near of potential_segment as possible
        potential_val = potential_segments # The most desired one 
    ) 

    if allow_crop: 
        if verbose > 1: print(f"[ Downsample | downsample_propose_crop ] Allow crop => change n_timestamp | Before {n_timestamps}")
        max_position = min_position + N
        if verbose > 1: print(f"[ Downsample | downsample_propose_crop ] Allow crop => change n_timestamp | After {n_timestamps}")
    
    data = data[min_position:max_position]
    n_timestamps = data.shape[0]

    if verbose > 0: 
        print(f"[ Downsample | downsample_propose_crop --> ] | N segments: {n_segments} | Data ~ {data.shape}")
        print(f"[ Downsample | downsample_propose_crop --> ] | N = {N} | n_timestamps = {n_timestamps} | min_position {min_position} | max_position {max_position}")

    if n_timestamps < max_points: 
        if verbose > 0: 
            print(f"[ Downsample ] n_timestamps {n_timestamps} < max_points {max_points}")
        return data, 1
        
    #| export
    paa_pipeline = Pipeline([
        (
            # Step for interpolating NaNs in the original data
            'interpolator', 
            Interpolator(
                method             = 'polynomial', 
                n_segments         = n_segments, 
                plot_original_data = show_plots,
                plot_interpolated  = show_plots
            )
        ),
        (
            # Step for applying Peicewise Aggregated Approximation
            'paa', PAATransformer(
                n_segments      = n_segments, 
                plot_aggregated = show_plots
            )
        )
    ])

    ts_paa = paa_pipeline.fit_transform(data[min_position:max_position])[0]
    if verbose > 0: 
        print(f"Downsample | ts_paa~{len(ts_paa)}")
        print(f"Downsample ------------------------>")
    return ts_paa, paa_factor


# %% ../nbs/utils.ipynb 80
import sys

# %% ../nbs/utils.ipynb 81
def print_flush(mssg, **kwargs):
    print(mssg, **kwargs)
    sys.stdout.flush()

# %% ../nbs/utils.ipynb 89
def find_dominant_window_sizes_list_single_old(
        X            : List [ float ],
        nsizes       : int  = 1,
        offset       : float= 0.05, 
        min_distance : int  = 1,
        verbose      : int  = 0
    ) -> List [ int ]:

    if verbose > 0: print( "---> Find_dominant_window_sizes_list" )
    if verbose > 1:
        print( "Find_dominant_window_sizes_list | X ~ ",  X.shape )
        print( "Find_dominant_window_sizes_list | Looking for - at most - the best", nsizes, "window sizes")
        print( "Find_dominant_window_sizes_list | Offset", offset, "max size:", offset*len(X))
    if verbose > 0: print( "Find_dominant_window_sizes_list | --> Freqs")
        
    X = np.array(X)
    
    fourier = np.absolute(np.fft.fft(X))   
    freqs = np.fft.fftfreq(X.shape[0], 1)
    
    if verbose > 1: 
        print( f"Find_dominant_window_sizes_list | Freqs {freqs} -->")
        print( f"Find_dominant_window_sizes_list | coefs {fourier} -->")
    if verbose > 0: print( f"Find_dominant_window_sizes_list | Freqs -->")

    coefs = []
    window_sizes = []

    for coef, freq in zip(fourier, freqs):
        if coef and freq > 0:
            coefs.append(coef)
            window_sizes.append(1 / freq)

    coefs = np.array(coefs)
    window_sizes = np.asarray(window_sizes, dtype=np.int64)
    
    if verbose > 0: 
        print( "Find_dominant_window_sizes_list | Coefs and window_sizes -->")
        print( "Find_dominant_window_sizes_list | --> Find and return valid window_sizes")

    idx = np.argsort(coefs)[::-1]
    
    if verbose > 1: 
        print( "Find_dominant_window_sizes_list | Find and return valid window_sizes | ... 0 ...", idx)
        
    sorted_window_sizes = window_sizes[idx]
    
    if verbose > 1: 
        print( "Find_dominant_window_sizes_list | Find and return valid window_sizes | ... 1 ...")

    # Find and return all valid window sizes
    valid_window_sizes = [
        int(window_size / 2) for window_size in sorted_window_sizes
        #if 20 <= window_size < int(X.shape[0] * offset)
        if 20 <= window_size < int(len(X) * offset)
    ]
    
    if verbose > 1: 
        print( "Find_dominant_window_sizes_list | Find and return valid window_sizes | ... 2 ...")

    # If no valid window sizes are found, return the first from sorted list
    if not valid_window_sizes:
        print( "Find_dominant_window_sizes_list | Find and return valid window_sizes | ... 2a ...", nsizes)
        sizes = [sorted_window_sizes[0] // 2][:nsizes]
    else:
        print( "Find_dominant_window_sizes_list | Find and return valid window_sizes | ... 2b ...", nsizes)
        sizes = valid_window_sizes[:nsizes]
        
    if verbose > 0: 
        print( "Find_dominant_window_sizes_list | Find and return valid window_sizes -->")
    if verbose > 1:
        print("Find_dominant_window_sizes_list | Sizes:", sizes)
    if verbose > 0:
        print( "Find dominant_window_sizes_list --->" )
    
    return sizes

# %% ../nbs/utils.ipynb 90
def select_separated_sizes(
    xs : List [ int ],
    min_distance : int = 1,
    nsizes          : int = 1
) -> List [ int ]:
    ys = []
    for window_size in xs:
        if not ys or abs(window_size - ys[-1]) >= min_distance:
            ys.append(window_size)
        if len(ys) == nsizes:
            break
    return ys

# %% ../nbs/utils.ipynb 92
def find_dominant_window_sizes_list_single(
        X            : List[float],
        nsizes       : int               = 1,
        offset       : float             = 0.05, 
        min_distance : int               = 1,    # Asegurar distancia mínima entre tamaños
        verbose      : int               = 0
    ) -> List[int]:

    if verbose > 0: print( "---> Find_dominant_window_sizes_list" )
    if verbose > 1:
        print( f"Find_dominant_window_sizes_list | X ~ {X.shape}" )
        print( f"Find_dominant_window_sizes_list | Looking for - at most - the best {nsizes} window sizes")
        print( f"Find_dominant_window_sizes_list | Offset {offset} max size: {offset*len(X)}")
    if verbose > 0: print( "Find_dominant_window_sizes_list | --> Freqs")
        
    X = np.array(X)
    
    fourier = np.absolute(np.fft.fft(X))   
    freqs = np.fft.fftfreq(X.shape[0], 1)
    
    if verbose > 2: 
        print( f"Find_dominant_window_sizes_list | Freqs {freqs} -->")
        print( f"Find_dominant_window_sizes_list | coefs {fourier} -->")
    if verbose > 0: print( f"Find_dominant_window_sizes_list | Freqs -->")

    coefs = []
    window_sizes = []

    for coef, freq in zip(fourier, freqs):
        if coef and freq > 0:
            coefs.append(coef)
            window_sizes.append(1 / freq)

    coefs = np.array(coefs)
    window_sizes = np.asarray(window_sizes, dtype=np.int64)
    
    if verbose > 0: 
        print( "Find_dominant_window_sizes_list | Coefs and window_sizes -->")
        print( "Find_dominant_window_sizes_list | --> Find and return valid window_sizes")

    idx = np.argsort(coefs)[::-1]
    
    if verbose > 1: 
        print( "Find_dominant_window_sizes_list | Find and return valid window_sizes | ... 0 ...", idx)
        
    sorted_window_sizes = window_sizes[idx]
    
    if verbose > 1: 
        print( "Find_dominant_window_sizes_list | Find and return valid window_sizes | ... 1 ...")

    # Find and return all valid window sizes
    valid_window_sizes = [
        int(window_size) for window_size in sorted_window_sizes
        if window_size < int(len(X) * offset)
    ]
    
    if verbose > 1: 
        print( "Find_dominant_window_sizes_list | Find and return valid window_sizes | ... 2 ...")

    # Ensure sizes separated at least at "min_distance" 
    sizes = select_separated_sizes(valid_window_sizes, min_distance, nsizes)

    # If no valid window sizes are found, return the first from sorted list
    if not sizes:
        print( "Find_dominant_window_sizes_list | Find and return valid window_sizes | ... 2a ...", nsizes)
        sizes = sorted_window_sizes[0][:nsizes]
    else:
        print( "Find_dominant_window_sizes_list | Find and return valid window_sizes | ... 2b ...", nsizes)

    if verbose > 0: 
        print( "Find_dominant_window_sizes_list | Find and return valid window_sizes -->")
    if verbose > 1:
        print("Find_dominant_window_sizes_list | Sizes:", sizes)
    if verbose > 0:
        print( "Find dominant_window_sizes_list --->" )
    
    return sizes


# %% ../nbs/utils.ipynb 95
def group_similar_sizes(vars_sizes, nsizes, tolerance=2):
    """
    Selects the best window sizes across multiple variables,
    ensuring no repetitions and that the sizes are sufficiently close.
    """
    indices = [0] * len(vars_sizes)  # Indices for each variable
    selected_sizes = []  # Selected window sizes

    while len(selected_sizes) < nsizes:
        # Get the smallest available size across all variables
        current_sizes = [vars_sizes[i][indices[i]] for i in range(len(vars_sizes)) if indices[i] < len(vars_sizes[i])]
        min_size = min(current_sizes)

        # Select sizes close to the minimum and avoid duplicates
        for i in range(len(vars_sizes)):
            if indices[i] < len(vars_sizes[i]) and abs(vars_sizes[i][indices[i]] - min_size) <= tolerance:
                if vars_sizes[i][indices[i]] not in selected_sizes:  # Avoid duplicates
                    selected_sizes.append(vars_sizes[i][indices[i]])
                indices[i] += 1  # Move to the next size for that variable

                if len(selected_sizes) >= nsizes:
                    break

        # End if no more sizes are left in any variable
        if all(idx >= len(vars_sizes[i]) for i, idx in enumerate(indices)):
            break

    # Remove duplicates from the selected sizes and return the first nsizes
    selected_sizes = list(dict.fromkeys(selected_sizes))  # Remove duplicates
    return selected_sizes[:nsizes]



# %% ../nbs/utils.ipynb 96
def find_dominant_window_sizes_list(
        X,
        nsizes          : int   = 1,
        offset          : float = 0.05, 
        verbose         : int   = 0,
        min_distance    : int   = 1
    ) -> List [ int ]:

    if verbose > 0:
        print_flush( f"---> Find_dominant_window_sizes_list" )
    
    if len(X.shape) == 1: 
        sizes = find_dominant_window_sizes_list_single(X,nsizes,offset, min_distance, verbose)
    else: 
        if ( isinstance(X, pd.DataFrame ) ): X = X.values
        if verbose > 0: print_flush( f"Find_dominant_window_sizes_list | X ~ {X.shape}" )
        vars_sizes = []
        for var in range( X.shape[1] ):
            if verbose > 1: print_flush( f"Find_dominant_window_sizes_list | Get sizes for var {var}" )
            var_sizes = find_dominant_window_sizes_list_single(X[:, var], nsizes, offset, min_distance, verbose)
            vars_sizes.append(var_sizes)
            if verbose > 1: 
                print_flush( f"Find_dominant_window_sizes_list | Get sizes for var {var} | {var_sizes}" )
        if verbose > 0: print_flush( f"Find_dominant_window_sizes_list | Grouping sizes" )
        sizes = group_similar_sizes(vars_sizes, nsizes, tolerance = 2)
        if verbose > 1:
            print_flush(f"find_dominant_window_sizes_list | Final selected window sizes: {sizes}")
    if verbose > 0: print_flush( f"Find_dominant_window_sizes_list -->" )
    return sizes
