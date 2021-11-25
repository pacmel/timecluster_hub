# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/load.ipynb (unless otherwise specified).

__all__ = ['TSArtifact', 'infer_or_inject_freq']

# Cell
import pandas as pd
import numpy as np
from fastcore.all import *
import wandb
from datetime import datetime, timedelta
from tchub.imports import *
from tchub.utils import *
import pickle

# Cell
class TSArtifact(wandb.Artifact):

    default_storage_path = Path(Path.home()/'data/wandb_artifacts/')
    date_format = '%Y-%m-%d %H:%M:%S' # TODO add milliseconds
    handle_missing_values_techniques = {
        'linear_interpolation': lambda df : df.interpolate(method='linear', limit_direction='both'),
        'overall_mean': lambda df : df.fillna(df.mean()),
        'overall_median': lambda df : df.fillna(df.median())
    }

    "Class that represents a wandb artifact containing time series data. sd stands for start_date \
    and ed for end_date. Both should be pd.Timestamps"

    @delegates(wandb.Artifact.__init__)
    def __init__(self, name, sd:pd.Timestamp, ed:pd.Timestamp, **kwargs):
        super().__init__(type='dataset', name=name, **kwargs)
        self.sd = sd
        self.ed = ed
        if self.metadata is None:
            self.metadata = dict()
        self.metadata['TS'] = dict(sd = self.sd.strftime(self.date_format),
                                   ed = self.ed.strftime(self.date_format))


    @classmethod
    def from_daily_csv_files(cls, root_path, fread=pd.read_csv, start_date=None, end_date=None, metadata=None, **kwargs):

        "Create a wandb artifact of type `dataset`, containing the CSV files from `start_date` \
        to `end_date`. Dates must be pased as `datetime.datetime` objects. If a `wandb_run` is \
        defined, the created artifact will be logged to that run, using the longwall name as \
        artifact name, and the date range as version."

        return None


    @classmethod
    @delegates(__init__)
    def from_df(cls, df:pd.DataFrame, name:str, path:str=None, sd:pd.Timestamp=None, ed:pd.Timestamp=None,
                normalize:bool=False, missing_values_technique:str=None, resampling_freq:str=None, **kwargs):

        """
        Create a TSArtifact of type `dataset`, using the DataFrame `df` samples from \
        `sd` (start date) to `ed` (end date). Dates must be passed as `datetime.datetime` \
        objects. The transformed DataFrame is stored as a pickle file in the path `path` \
        and its reference is added to the artifact entries. Additionally, the dataset can \
        be normalized (see `normalize` argument) or transformed using missing values \
        handling techniques (see `missing_values_technique` argument) or resampling (see \
        `resampling_freq` argument).

        Arguments:
            df: (DataFrame) The dataframe you want to convert into an artifact.
            name: (str) The artifact name.
            path: (str, optional) The path where the file, containing the new transformed \
                dataframe, is saved. Default None.
            sd: (sd, optional) Start date. By default, the first index of `df` is taken.
            ed: (ed, optional) End date. By default, the last index of `df` is taken.
            normalize: (bool, optional) If the dataset values should be normalized. Default\
                False.
            missing_values_technique: (str, optional) The technique used to handle missing \
                values. Options: "linear_iterpolation", "overall_mean", "overall_median" or \
                None. Default None.
            resampling_freq: (str, optional) The offset string or object representing \
                frequency conversion for time series resampling. Default None.

        Returns:
            TSArtifact object.
        """
        sd = df.index[0] if sd is None else sd
        ed = df.index[-1] if ed is None else ed
        obj = cls(name, sd=sd, ed=ed, **kwargs)
        df = df.query('@obj.sd <= index <= @obj.ed')
        obj.metadata['TS']['created'] = 'from-df'
        obj.metadata['TS']['n_vars'] = df.columns.__len__()

        # Handle Missing Values
        df = obj.handle_missing_values_techniques[missing_values_technique](df) if missing_values_technique is not None else df
        obj.metadata['TS']['handle_missing_values_technique'] = missing_values_technique.__str__()
        obj.metadata['TS']['has_missing_values'] = np.any(df.isna().values).__str__()

        # Indexing and Resampling
        if resampling_freq: df = df.resample(resampling_freq).mean()
        obj.metadata['TS']['n_samples'] = len(df)
        obj.metadata['TS']['freq'] = str(df.index.freq)

        # Time Series Variables
        obj.metadata['TS']['vars'] = list(df.columns)

        # Normalization - Save the previous means and stds
        if normalize:
            obj.metadata['TS']['normalization'] = dict(means = df.describe().loc['mean'].to_dict(),
                                                       stds = df.describe().loc['std'].to_dict())
            df = normalize_columns(df)

        # Hash and save
        hash_code = str(hash(df.values.tobytes()))
        path = obj.default_storage_path/f'{hash_code}' if path is None else Path(path)/f'{hash_code}'
        df.to_pickle(path)
        obj.metadata['TS']['hash'] = hash_code
        obj.add_file(str(path))

        return obj

# Cell
@patch
def to_df(self:wandb.apis.public.Artifact):
    "Download the files of a saved wandb artifact and process them as a single dataframe. The artifact must \
    come from a call to `run.use_artifact` with a proper wandb run."
    # The way we have to ensure that the argument comes from a TS arfitact is the metadata
    if self.metadata.get('TS') is None:
        print(f'ERROR:{self} does not come from a logged TSArtifact')
        return None
    dir = Path(self.download())
    if self.metadata['TS']['created'] == 'from-df':
        # Call read_pickle with the single file from dir
        return pd.read_pickle(dir.ls()[0])
    else:
        print("ERROR: Only from_df method is allowed yet")

# Cell
@patch
def to_tsartifact(self:wandb.apis.public.Artifact):
    "Cast an artifact as a TS artifact. The artifact must have been created from one of the \
    class creation methods of the class `TSArtifact`. This is useful to go back to a TSArtifact \
    after downloading an artifact through the wand API"
    return TSArtifact(name=self.digest, #TODO change this
                      sd=pd.to_datetime(self.metadata['TS']['sd'], format=TSArtifact.date_format),
                      ed=pd.to_datetime(self.metadata['TS']['sd'], format=TSArtifact.date_format),
                      description=self.description,
                      metadata=self.metadata)

# Cell
def infer_or_inject_freq(df, injected_freq='1s'):
    """
        Infer index frequency. If there's not a proper time index, create fake timestamps,
        keeping the desired `injected_freq`. If that is None, set a default one of 1 second
    """
    inferred_freq = pd.infer_freq(df.index)
    if inferred_freq == 'N':
        timedelta = pd.to_timedelta(injected_freq)
        df.index = pd.to_datetime(0) + timedelta*df.index
        df.index.freq = injected_freq
    else:
        df.index.freq = inferred_freq
    return df