# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/mplots.ipynb.

# %% auto 0
__all__ = ['eamonn_drive_mplots', 'MatrixProfile', 'matrix_profile', 'compute', 'MatrixProfiles', 'plot_dataFrame',
           'plot_dataFrame_compareSubsequences', 'df_plot_colored_variables', 'plot_df_with_intervals_and_colors',
           'plot_motif', 'plot_motif_separated', 'GD_Mat', 'MatrixProfilePlot']

# %% ../nbs/mplots.ipynb 4
## -- Deepvats
import dvats.load as load
import dvats.memory as mem
import dvats.utils as ut

## -- Matrix profile
import pyscamp as scamp
import stumpy as stump 
## -- Utilities
import os
import numpy as np
import pandas as pd
import datetime as dt
## -- Classes & types
from dataclasses import dataclass, field
from typing import List
## -- Plotting
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as dates

from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle

from mpl_toolkits.axes_grid1 import ImageGrid
from copy import deepcopy
plt.style.use('https://raw.githubusercontent.com/TDAmeritrade/stumpy/main/docs/stumpy.mplstyle')


# %% ../nbs/mplots.ipynb 6
@dataclass
class MatrixProfile:
    """ Class for better usability of Matrix Profile inside deepVATS"""
    #---- Main information of the matrix profile ----#
    #-- Matrix Profile (distance array)
    matrix_profile: List[float] =  field(default_factory=list)

    # Execution information
    computation_time: float = 0.0
    
    #-- Size used for the MP computation
    subsequence_len: int = 0
    #-- Wether if stumpy or SCAMP or other method have been used 
    method: str = ''
    
    #-- Looking for motifs & neighbors
    # Ordered array for finding motifs/anomalies
    index : List[int] =  field(default_factory=list)
    # Nearest neighbours in the past (if computed)
    index_left : List[int] =  field(default_factory=list)
    # Nearest neighbours in the future (if computed)
    index_right: List[int] = field(default_factory=list)

    #--- Save the main motif index and its neighbors' index    
    motif_idx: int = 0
    motif_nearest_neighbor_idx: int = 0
    motif_nearest_neighbor_idx_left: int = 0
    motif_nearest_neighbor_idx_right: int = 0

    #--- Save the main anomaly index and its neighbors' index
    discord_idx: int = 0
    discord_nearest_neighbor_idx: int = 0
    discord_nearest_neighbor_idx_left: int = 0
    discord_nearest_neighbor_idx_right: int = 0
    
    def __str__(self):
        return f"MP: {self.matrix_profile}\nIds: {self.index}\nIds_left: {self.index_left}\nIds_right: {self.index_right}\nComputation_time: {self.computation_time}\nsubsequence_len: {self.subsequence_len}\nmethod: {self.method}"

# %% ../nbs/mplots.ipynb 8
def matrix_profile(
    data, 
    subsequence_len, 
    data_b     = None,
    method     = 'scamp', 
    threads    = 4, # For scamp abjoin
    gpus       = [], # For scamp abjoin
    print_flag = False, 
    debug      = True, 
    timed      = True
):
    """ 
    This function 
    Receives
    - data: a 1D-array representing a time series values (expected to be long)
    - subsequence_len: Matrix Profile subsequences length
    - method: wether to use stump or scamp algorithm
    - print_flag: for printing or not messages
    - debug: for adding some comprobations on GPUs usability
    - timed: for getting or not the execution time for the implementation analysis
    - Threads: number of threads for scamp multithread execution
    - GPUs: id of the GPUs to be used for scamp execution

    and returns 
    - mp: matrix profile
    - index: patterns indices
    - index_left: nearest neighbors in the past
    - index_right: nearest neigbhbors in the future
    """
    
    if print_flag: print("--> matrix profile")
    #Execution time
    duration = 0.0
    # Matrix Profile (distances)
    mp = []
    # Patterns indices (position within the MP)
    index = []
    index_left = []
    index_right = []
    
    #-- Start timing
    if timed: 
        timer = ut.Time()
        timer.start()

    #-- Select the method
    match method:
        case 'stump': # Not tested
            #-- use stumpy.gpu_stump
            if print_flag: print("--> Stump (CPU)")
            mp = stump.stump(data, subsequence_len, data_b)
            #-- Save in separated columns for compatibility with SCAMP
            index = mp[:,1]
            index_left = mp[:,2]
            index_right = mp[:,3]
            mp = mp[:,0]
        
        case 'stump_gpu': # You are suposed to use this or scamp
            if print_flag: print("--> Stump (GPU)")
            #-- Matrix profile
            mp = stump.gpu_stump(data, subsequence_len, data_b)
            #-- Save in separate columns
            index = mp[:,1]
            index_left = mp[:,2]
            index_right = mp[:,3]
            mp = mp[:,0]
            
        case 'scamp': # Yo should use GPU in Large TS
            if print_flag: print("--> Scamp")
            if debug: 
                print("Check gpu use")
                has_gpu_support = scamp.gpu_supported()
                print(has_gpu_support)
            #-- Matrix profile & index. Nothing more to save
            if (data_b is None):
                mp, index = scamp.selfjoin(data, subsequence_len)
            else: 
                if print_flag: print("--> data_b provided => Executing abjoin")
                mp, index = scamp.abjoin(data, data_b, subsequence_len, threads, gpus)
        case _: #default scamp
            if print_flag: print("--> Invalid method. Using scamp [default]")
            if debug: 
                has_gpu_support = scamp.gpu_supported()
                print(has_gpu_support)
            if data_b is None:
                mp, index = scamp.selfjoin(data, subsequence_len)
            else:
                if print_flag: print("--> data_b provided => Executing abjoin")
                mp, index = scamp.abjoin(data, data_b, subsequence_len, threads, gpus)
    if timed: 
        timer.end()
        duration = timer.duration() 
    if print_flag: 
        if timed: 
            print(f"matrix profile {duration} seconds -->")
        else: 
            print("matrix profile -->")
    return mp, index, index_left, index_right, duration

# %% ../nbs/mplots.ipynb 10
def compute(
    self : MatrixProfile, 
    data : List[float],
    subsequence_len : int, 
    data_b : List[float] = None,
    method : str = 'scamp',  
    threads : int = 1,
    gpus : List[int] = [],
    print_flag : bool = False, 
    debug : bool = False, 
    timed :bool = True
):
    if print_flag: print("Subsequence len: ", subsequence_len)
    self.subsequence_len = subsequence_len
    self.method = method
    self.matrix_profile, self.index, self.index_left, self.index_right, self.computation_time = matrix_profile(
        data, subsequence_len, data_b, method, threads, gpus, print_flag, debug, timed
    )
    return self.matrix_profile
MatrixProfile.compute = compute

# %% ../nbs/mplots.ipynb 15
@dataclass
class MatrixProfiles:
    matrix_profiles: List[MatrixProfile] =  field(default_factory=list)
    data: List[float] = field(default_factory=list)
    data_b : List[float] = None
    
    subsequence_len: int = 0

    def append(self, mp: MatrixProfile):
        self.matrix_profiles.append(deepcopy(mp))
        self.subsequence_len = mp.subsequence_len
    def compute(
        self, 
        method : str      = 'scamp',  
        threads: int      = 1,
        gpus : List[int]  = field(default_factory=list),
        print_flag : bool = False, 
        debug : bool      = False, 
        timed : bool      = True
    ):
        """ 
        Computes the Matrix Profile for data & data_b arrays using subsequence_len length.
        Appends the resulting MP to the matrix_profiles list.
        """
        mp = MatrixProfile()
        mp.compute(
            data            = self.data, 
            subsequence_len = self.subsequence_len, 
            data_b          = self.data_b,
            method          = method, 
            threads         = threads,
            gpus            = gpus,
            print_flag      = print_flag, 
            debug           = debug, 
            timed           = timed
        )
        
        mp.method = method
        if print_flag: 
            print("MPs | compute -> Subsequence len out: ", self.subsequence_len)
            print("MPs | compute -> Subsequence len inside: ", mp.subsequence_len)
        self.matrix_profiles.append(mp)
        return mp
    
    def plot(self, ids = []):
        if ids == []: ids = range(len(self.matrix_profiles))
        num_plots = len(ids)+1
        fig = plt.figure(figsize=(10, 6))
        gs = GridSpec(num_plots, 1, height_ratios=[1] + [4] * (num_plots -1))
        # Serie temporal
        ax1 = fig.add_subplot(gs[0])
        ax1.plot(self.data, label="Data")
        ax1.set_title("Time Serie")
        ax1.legend()
        # MPlots
        for i in ids:
            ax2 = fig.add_subplot(gs[i+1], sharex=ax1)
            mp_values = self.matrix_profiles[i].matrix_profile.astype(float)
            ax2.imshow(mp_values.reshape(-1, 1).T, aspect='auto', origin='lower', cmap='hot', extent=(0, len(self.data), 0, self.subsequence_len))
            ax2.set_title(f"MPlot - {i} - {self.matrix_profiles[i].method}")
        plt.tight_layout()
        plt.show()

    def get_ordered_idx(self, id, pos):
        mp_sorted = np.argsort( self.matrix_profiles[id].matrix_profile )
        return mp_sorted[pos]
        
    def get_motif_idx(self, id): 
        motif_idx = self.get_ordered_idx(id, 0)
        self.matrix_profiles[id].motif_idx = motif_idx
        self.matrix_profiles[id].motif_nearest_neighbor_idx = self.matrix_profiles[id].index[motif_idx]
        
        if ( self.matrix_profiles[id].method == 'stump' ):
            self.matrix_profiles[id].motif_nearest_neighbor_idx_left = self.matrix_profiles[id].index_left[motif_idx]
            self.matrix_profiles[id].motif_nearest_neighbor_idx_right = self.matrix_profiles[id].index_right[motif_idx]
        return self.matrix_profiles[id].motif_idx, self.matrix_profiles[id].motif_nearest_neighbor_idx, self.matrix_profiles[id].motif_nearest_neighbor_idx_left, self.matrix_profiles[id].motif_nearest_neighbor_idx_right
    
    def get_anomaly_idx(self, id): 
        discord_idx = self.get_ordered_idx(id, -1)
        self.matrix_profiles[id].discord_idx = discord_idx
        self.matrix_profiles[id].discord_nearest_neighbor_idx = self.matrix_profiles[id].index[discord_idx]
        
        if ( self.matrix_profiles[id].method == 'stump' ):
            self.matrix_profiles[id].discord_nearest_neighbor_idx_left = self.matrix_profiles[id].index_left[discord_idx]
            self.matrix_profiles[id].discord_nearest_neighbor_idx_right = self.matrix_profiles[id].index_right[discord_idx]
            
        return self.matrix_profiles[id].discord_idx, self.matrix_profiles[id].discord_nearest_neighbor_idx, self.matrix_profiles[id].discord_nearest_neighbor_idx_left, self.matrix_profiles[id].discord_nearest_neighbor_idx_right
    
    
    def plot_motif(
        self, 
        ts_name,
        id, 
        idx, 
        nearest_neighbor_idx, 
        title_fontsize = '30', 
        other_fontsize = '20'
    ): 
        fig, axs = plt.subplots(2, sharex=True, gridspec_kw={'hspace': 0.4})
        plt.suptitle('Motif (Pattern) Discovery | ' + self.matrix_profiles[id].method , fontsize=title_fontsize)

        axs[0].plot(self.data.values)
        axs[0].set_ylabel(ts_name, fontsize=other_fontsize)
        rect = Rectangle((idx, 0), self.subsequence_len, 40, facecolor='lightgrey')
        axs[0].add_patch(rect)
        rect = Rectangle((nearest_neighbor_idx, 0), self.subsequence_len, 40, facecolor='lightgrey')
        axs[0].add_patch(rect)
        axs[1].set_xlabel('Index', fontsize =other_fontsize)
        axs[1].set_ylabel('Matrix Profile', fontsize=other_fontsize)
        axs[1].axvline(x=idx, linestyle="dashed", color = "black")
        axs[1].axvline(x=nearest_neighbor_idx, linestyle="dashed", color="red")
        axs[1].plot(self.matrix_profiles[id].matrix_profile)
        plt.show()
        
        


# %% ../nbs/mplots.ipynb 25
def plot_dataFrame(title, df, vars = [], interval = 10000):
    if len(vars) > 0:
        num_vars = len(df.columns)
    
        for var_num in vars:
            if var_num >= len(df.columns):
                raise ValueError("var_num "+var[var_num] + "is out of the range of DataFrame columns: " + num_vars)

        num_vars = len(vars)
        
        ### Start the plot 

        #fig = plt.figure(figsize=(10, num_intervals * 3))  # Ajusta el tamaño del plot según el número de intervalos
        
        num_intervals = df.shape[0] // interval + 1
        fig = plt.figure(figsize=(10, num_vars * num_intervals * 3))  ## Size
        gs = GridSpec(num_intervals*num_vars, 1) # 1 column, len(vars) rows
        var_pos = 0
        for var_num  in vars:
            var_name = df.columns[var_num]
            data = df[var_name]
            for i in range(num_intervals):    
                start_idx = i * interval
                end_idx = len(data) if i == (num_intervals - 1) else start_idx + interval
                ax = fig.add_subplot(gs[var_pos+i])
                ax.plot(np.arange(start_idx, end_idx), data[start_idx:end_idx], label=f"{var_name} [{start_idx}, {end_idx}]")
                ax.set_title(f"{var_name} [{start_idx}, {end_idx}]")
                ax.set_xlabel("Time")
                ax.set_ylabel(var_name)
                ax.legend()
            var_pos += 1
                
        plt.suptitle(title, fontsize=16)
        plt.tight_layout()
        plt.show()
    else: raise ValueError("No variable proposed for plotting")

# %% ../nbs/mplots.ipynb 26
def plot_dataFrame_compareSubsequences(
    title, df, var, subsequence_len, seq1_init, seq2_init, 
    title_fontsize = '30',
    others_fontsize='20'
):
    fig, axs = plt.subplots(2)
    fig.subplots_adjust(hspace=0.4) 
    plt.suptitle(title, fontsize=title_fontsize)
    var_name = df.columns[var]
    axs[0].set_ylabel(var_name, fontsize=others_fontsize)
    axs[0].plot(df[var_name], alpha=0.5, linewidth=1)
    axs[0].plot(df[var_name].iloc[seq1_init:seq1_init+subsequence_len])
    axs[0].plot(df[var_name].iloc[seq2_init:seq2_init+subsequence_len])
    rect = Rectangle((seq1_init, 0), subsequence_len, 40, facecolor='lightgrey')
    axs[0].add_patch(rect)
    axs[0].set_xlabel("Index", fontsize=others_fontsize)

    rect = Rectangle((seq2_init, 0), subsequence_len, 40, facecolor='lightgrey')
    axs[0].add_patch(rect)
    axs[1].set_xlabel("Relative Index (subsequence)", fontsize=others_fontsize)
    axs[1].set_ylabel(var_name, fontsize=others_fontsize)
    axs[1].plot(df[var_name].values[seq1_init:seq1_init+subsequence_len], color='C1')
    axs[1].plot(df[var_name].values[seq2_init:seq2_init+subsequence_len], color='C2')
    plt.show()
    

# %% ../nbs/mplots.ipynb 28
def df_plot_colored_variables(df):
    # Show time series plot
    fig, ax = plt.subplots(1, figsize=(15,5), )
    cmap = matplotlib.colormaps.get_cmap('viridis')
    #df.plot(color=cmap(0.05), ax=ax) # or use colormap=cmap
    df.plot(colormap=cmap, ax=ax) # or use colormap=cmap
    # rect = Rectangle((5000, -4.2), 3000, 8.4, facecolor='lightgrey', alpha=0.5)
    # ax.add_patch(rect)
    plt.tight_layout()
    plt.legend()
    display(plt.show())

# %% ../nbs/mplots.ipynb 29
def plot_df_with_intervals_and_colors(title, df, interval=10000):
    num_variables = len(df.columns)
    num_intervals = len(df) // interval + 1  # Calcula el número necesario de intervalos/subplots

    fig = plt.figure(figsize=(10, num_intervals * 3 * num_variables))  # Ajusta el tamaño del plot
    gs = GridSpec(num_intervals * num_variables, 1)
    
    cmap = matplotlib.colormaps.get_cmap('viridis')

    for var_num, var in enumerate(df.columns):
        data = df[var]
        for i in range(num_intervals):
            ax = fig.add_subplot(gs[var_num * num_intervals + i])
            start_idx = i * interval
            end_idx = start_idx + interval

            if i == num_intervals - 1:  # Ajusta el último intervalo para incluir todos los datos restantes
                end_idx = len(data)

            color = cmap(var_num / num_variables)  # Asigna un color basado en la variable
            ax.plot(np.arange(start_idx, end_idx), data[start_idx:end_idx], label=f"{var} [{start_idx}, {end_idx}]", color=color)
            ax.set_title(f"{var} [{start_idx}, {end_idx}]")
            ax.set_xlabel("Index")
            ax.set_ylabel(var)
            ax.legend()

    plt.suptitle(title, fontsize=16)
    plt.tight_layout()
    plt.show()

# %% ../nbs/mplots.ipynb 30
def plot_motif(df, motif_idx, nearest_neighbor_idx, variable_name, title, padding = 1000, m = 1, mp = None):
    fig, axs = plt.subplots(2, sharex = True, gridspec_kw={'hspace': 0})
    plt.suptitle('Motif (Pattern) Discovery', fontsize='30')
    padding = min(padding, len(df[variable_name].values) // 2)

    # Calcula los límites para hacer zoom
    x_min = max(min(motif_idx, nearest_neighbor_idx) - padding, 0)
    x_max = min(max(motif_idx, nearest_neighbor_idx) + padding, len(df[variable_name].values))

    axs[0].plot(df[variable_name].values)
    axs[0].set_xlim([x_min, x_max])  # Aplica el zoom aquí
    axs[0].set_ylabel(title, fontsize='20')
        
    axs[0].set_ylabel(title, fontsize='20')
    rect = Rectangle((motif_idx, 0), m, 40, facecolor='lightgrey')
    axs[0].add_patch(rect)
    rect = Rectangle((nearest_neighbor_idx, 0), m, 40, facecolor='lightgrey')
    axs[0].add_patch(rect)
    axs[1].set_xlabel('Time', fontsize ='20')
    axs[1].set_ylabel('Matrix Profile', fontsize='20')
    axs[1].axvline(x=motif_idx, linestyle="dashed")
    axs[1].axvline(x=nearest_neighbor_idx, linestyle="dashed")
    axs[1].plot(mp)
    plt.show()

# %% ../nbs/mplots.ipynb 31
def plot_motif_separated(df, motif_idx=0, nearest_neighbor_idx=0, variable_name="", title="", padding=1000, m=1, mp=None):
    fig, axs = plt.subplots(4, sharex=False, figsize=( 12, 5), gridspec_kw={'hspace': 0.5})
    plt.suptitle('Motif (Pattern) Discovery', fontsize='20')
    
    padding = max(m, min(padding, len(df[variable_name].values) // 2))

    x_min_motif = max(motif_idx - padding, 0)
    x_max_motif = min(motif_idx + padding, len(df[variable_name].values))

    axs[0].plot(df[variable_name].values)
    axs[0].set_xlim([x_min_motif, x_max_motif])
    axs[0].set_ylabel(title, fontsize='10')
    rect_motif = Rectangle((motif_idx, df[variable_name].min()), m, df[variable_name].max() - df[variable_name].min(), facecolor='lightgrey')
    axs[0].add_patch(rect_motif)

    axs[1].plot(mp)
    axs[1].set_xlim([x_min_motif, x_max_motif])
    axs[1].set_xlabel('Time', fontsize='10')
    axs[1].set_ylabel('MP - Min', fontsize='10')
    axs[1].axvline(x=motif_idx, linestyle="dashed")

    x_min_neighbor = max(nearest_neighbor_idx - padding, 0)
    x_max_neighbor = min(nearest_neighbor_idx + padding, len(df[variable_name].values))

    axs[2].plot(df[variable_name].values)
    axs[2].set_xlim([x_min_neighbor, x_max_neighbor])
    axs[2].set_ylabel(title, fontsize='10')
    rect_neighbor = Rectangle((nearest_neighbor_idx, df[variable_name].min()), m, df[variable_name].max() - df[variable_name].min(), facecolor='lightgrey')
    axs[2].add_patch(rect_neighbor)

    axs[3].plot(mp)
    axs[3].set_xlim([x_min_neighbor, x_max_neighbor])
    axs[3].set_xlabel('Time', fontsize='10')
    axs[3].set_ylabel('MP-max', fontsize='10')
    axs[3].axvline(x=nearest_neighbor_idx, linestyle="dashed")

    plt.show()

# %% ../nbs/mplots.ipynb 33
class GD_Mat:
    def __init__(self, id,  name, data_path = '~/data'):
        self.id = id
        self.data_path = os.path.expanduser(data_path)
        self.zip_path = os.path.join(self.data_path, name + '.zip')
        self.mat_path = os.path.join(self.data_path, name + '.mat')
        self.mats_files = None
        self.mats = None
        self.mats_df =  None
        self.num_mats = 0
        self.num_mats_extracted = 0
        
    def download_file_from_google_drive(self):
        return load.download_file_from_google_drive(self.id, self.zip_path)
        
    def get_mat_files(self):
        self.mats_files = [f for f in load.zip_contents(self.zip_path) if not f.startswith('__MACOSX/')]
        self.num_mats = len(self.mats_files)
        self.mats = self.mats_df = [None]*self.num_mats
    
    def unzip_mat(self, all_one, case = '', print_flag = False): 
        str = load.unzip_mat(all_one, self.zip_path, self.data_path, case, print_flag)
        self.get_mat_files()
        return str
        
    def mat2csv(self, case_id, print_flag = False):
        if print_flag: print("--> mat2csv", case_id)
        case = self.mats_files[case_id]
        case_path = os.path.join(self.data_path, case)
        print("Mat2csv case", case_path)
        self.mats_df[case_id] = load.mat2csv(case_path, self.data_path, print_flag)
        if print_flag: print("mat2csv", case_id, "-->")
        
    def __str__(self): 
        str = f"FileID: {self.id}\nData path: {self.data_path}\n"
        str += f"zip path: {self.zip_path}\nmat_files: {self.mats_files}"
        str +=f"\nnum_mats: {self.num_mats}"
        return str
    

# %% ../nbs/mplots.ipynb 36
@dataclass
class MatrixProfilePlot:
    """ Time series similarity matrix plot """
    similarity_matrix : List[ List [ float ]] = field(default_factory=list)
    data: np.array = field(default_factory=list)
    subsequence_len: int = 0
    def compute_similarity_matrix(
        self,
        subsequence_len : int = 0,
        reference_seq : List[float] = None, 
        method = 'scamp',
        timed : bool = True, 
        print_flag : bool = False
    ) -> List [ List [ float ] ] :
        complete = reference_seq == None
        n = len(self.data)
        self.subsequence_len = subsequence_len
        rows = n - subsequence_len + 1
        if (complete): 
            columns = rows
            reference_seq = self.data
        else: 
            columns = len(reference_seq) + 1
        self.similarity_matrix = np.empty((rows, columns))
        if timed: 
            timer = Time()
            timer.start()
        match method:
            case 'stump':
                if print_flag: print("--> Stump")
                for i in range(n - self.subsequence_len + 1):
                    self.similarity_matrix[i,:] =  stump.core.mass(
                        self.data[i:i + self.subsequence_len], reference_seq
                    ) 
                        
            case 'scamp': 
                if print_flag: print("--> Scamp")
                if complete:
                    self.similarity_matrix = scamp.selfjoin_matrix(
                        self.data, 
                        self.subsequence_len,
                        gpus = [],
                        mheight = n - self.subsequence_len + 1,
                        mwidth = n - self.subsequence_len + 1,
                        verbose = print_flag,
                        pearson = True
                    )
                    if print_flag: print("--> Complete ", self.similarity_matrix.shape)
                else: 
                    for i in range(n - self.subsequence_len + 1):
                        self.similarity_matrix[i, :] = scamp.abjoin(
                            reference_seq, 
                            self.data[i:i + self.subsequence_len],
                            self.subsequence_len
                        )[0]
                        
            case _: #default scamp
                if print_flag: print("--> Invalid method. Using scamp [default]")
                for i in range(n - self.subsequence_len + 1):
                    self.similarity_matrix[i, :] = scamp.abjoin(
                        reference_seq, 
                        self.data[i:i + self.subsequence_len],
                        self.subsequence_len
                    )[0]
                #if print_flag: print("--> Scamp")
                #self.similarity_matrix, _ = scamp.selfjoin(self.data, self.subsequence_len)
        if timed: 
            timer.end()
            duration = timer.duration() 
        if print_flag: 
            if timed: 
                print(f"matrix profile {duration} seconds -->")
            else: 
                print("matrix profile -->")
        return self.similarity_matrix

    def plot(self, ts_name, method = 'Scamp'):
        fig = plt.figure(figsize=(10, 10))
        gs = GridSpec(2, 1, height_ratios=[1, 4])

        # Serie temporal
        ax1 = fig.add_subplot(gs[0])
        ax1.plot(self.data, label="Time Serie")
        ax1.set_title(ts_name + " | " +  method)
        ax1.legend()

        # MPlot
        ax2 = fig.add_subplot(gs[1], sharex=ax1)
        # Utilizar 'imshow' para visualizar la matriz MPlot
        ax2.imshow(self.similarity_matrix, aspect='auto', origin='lower', cmap='hot', extent=(0, len(self.data) - self.subsequence_len, 0, len(self.data) - self.subsequence_len))
        ax2.set_title("MPlot")
        ax2.set_xlabel('Subsecuencia Inicial')
        ax2.set_ylabel('Subsecuencia Referencia')

        plt.tight_layout()
        plt.show()

# %% ../nbs/mplots.ipynb 40
eamonn_drive_mplots = {
    'insects0': {
        'id': '1qq1z2mVRd7PzDqX0TDAwY7BcWVjnXUfQ',
        'name': 'InsectData-fig11'
    }
}
