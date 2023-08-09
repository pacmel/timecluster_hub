import utils.errors
import os
import yaml
import sys
sys.path.append(os.path.abspath('..'))
from tsai.basics import *

### Only if !join not defined -- start
def join_constructor(loader, node):
    seq = loader.construct_sequence(node)
    return ''.join(seq)
##### -- end




def recursive_attrdict(d):
    """ Recursively converts a dictionary into an AttrDict, including all nested dictionaries. """
    if isinstance(d, dict):
        return AttrDict({k: recursive_attrdict(v) for k, v in d.items()})
    return d

def get_config(print_flag=False):
    yaml.add_constructor('!join', join_constructor)
    full_content = replace_includes_with_content(filename, path)
    config = yaml.load(full_content, Loader=yaml.FullLoader)
    return recursive_attrdict(config)


def get_project_data(print_flag):
    config      = get_config()
    project     = config.wandb.project
    user        = config.wandb.user
    version     = config.wandb.version
    data_name   = config.data.name
    data        = data_name + ':v' +version
    if print_flag:
        dashes = '-----------'        
        print(dashes+"Project configuration"+dashes)
        print("user: " + user)
        print("project: " + project)
        print("version: " + version)
        print("data: "+ data)
        print(dashes+"Project configuration"+dashes)
    return user, project, version, data

def get_train_artifact(user, project, data):
    # entity/project/name:version
    train_artifact=user+'/'+project+'/'+data 
    return train_artifact

#MVP ENCODER
def get_artifact_config_MVP_auxiliar_variables(print_flag):
    #Get neccesary variables
    user, project, version, data = get_project_data(print_flag)
    config          = get_config(print_flag, "02a-encoder_mvp")
    user_preferences = config.user_preferences
    config = config.configuration
    train_artifact_ = get_train_artifact(user,project,data)    
    mvp_ws1         = config.artifact_MVP.mvp_ws1
    mvp_ws2         = config.artifact_MVP.mvp_ws2
    mvp_ws = (mvp_ws1,mvp_ws2)
    return user, project, version, data, config, train_artifact_, mvp_ws, user_preferences

def check_project_and_entity(user, project):
    os_entity = os.environ['WANDB_ENTITY']
    os_project = os.environ['WANDB_PROJECT']
    if (os_entity != user):
        custom_error("Please check .env and base.yml: entity != user os " + os_entity + " yaml " + user)
    if (os_project != project):
        custom_error("Please check .env and base.yml: project differs os " + os_project + " yaml " + project)


def get_artifact_config_MVP_check_errors(artifact_config, user, project):
    check_project_and_entity(user, project)
        
    if artifact_config.use_wandb:
        if (artifact_config.analysis_mode != 'online'):
            print("Changing to online analysis mode - use_wandb=true")
            artifact_config.analysis_mode = 'online'
    else:
        project = 'work-nbs'

def get_artifact_config_MVP(print_flag=False):
    user, project, version, data, config, train_artifact_, mvp_ws, user_preferences = get_artifact_config_MVP_auxiliar_variables(print_flag)
    artifact_config = AttrDict(
        alias                   = config.alias,
        analysis_mode           = config.wandb.mode, 
        batch_size              = artifact.batch_size,
        epochs                  = artifact.n_epoch,
        mask_future             = bool(artifact.mask_future),
        mask_stateful           = bool(artifact.mask_stateful),
        mask_sync               = bool(artifact.mask_sync),
        mvp_ws                  = mvp_ws, 
        norm_by_sample          = artifact.norm_by_sample,
        norm_use_single_batch   = artifact.norm_use_single_batch,
        r                       = artifact.r,
        stride                  = artifact.stride, 
        train_artifact          = train_artifact_, 
        use_wandb               = user_preferences.use_wandb, 
        valid_size              = config.specifications.mvp.valid_size,
        w                       = config.specifications.sliding_windows.size, 
        wandb_group             = config.wandb.group
    )
    get_artifact_config_MVP_check_errors(artifact_config, user, project)
    return user, project, version, data, artifact_config, config.job_type

##############################
# 01 - DATAFRAME TO ARTIFACT #
##############################

def get__artifact_config_sd2a_get_auxiliar_variables(print_flag):
    user, project, version, data = get_project_data(print_flag)
    config      = get_config()
    data        = config.data
    use_wandb   = config.user_preferences.use_wandb
    wandb_path  = config.wandb.artifacts_path
    return user, project, version, data, use_wandb, wandb_path

def get__artifact_config_sd2a_check_errors(use_wandb, artifact_config, user, project):
    check_project_and_entity(user, project)
    if (
            use_wandb   == "offline" 
        and artifact_config.joining_train_test  == True
    ):
        custom_error("If you're using deepvats in offline mode, set joining_train_test to False")
    if (
            artifact_config.missing_values_constant is not None 
        and artifact_config.missing_values_technique is None
    ):
        custom_error("Missing values constant must be setted up only if missing_values_technique is not None. Please check base.yaml")

def get_artifact_config_sd2a(print_flag=False):
    user, project, version, data, use_wandb, wandb_path = get__artifact_config_sd2a_get_auxiliar_variables(print_flag)
    artifact_config = AttrDict(
        artifact_name           = data.alias,
        csv_config              = data.csv_config,
        data_cols               = data.cols,
        data_fpath              = data.path,
        date_format             = data.date_format,
        date_offset             = data.date_offset,
        freq                    = data.freq,
        joining_train_test      = bool(data.joining_train_test),
        missing_values_technique= data.missing_values.technique,
        missing_values_constant = data.missing_values.constant,
        normalize_training      = data.normalize_training,
        range_training          = data.range_training,
        range_testing           = data.range_testing,
        resampling_freq         = data.resampling_freq,
        start_date              = data.start_date,
        test_split              = data.test_split,
        time_col                = data.time_col,
        use_wandb               = use_wandb,
        wandb_artifacts_path    = wandb_path
    )
    get__artifact_config_sd2a_check_errors(use_wandb, artifact_config, user, project)    
    return artifact_config

######################
# 02a - ENCODER DCAE #
######################
def get_artifact_config_DCAE(print_flag=False):
    config = get_config(print_flag, "02b-encoder_dcae")
    print("Antes de leer configuration " + str(config))
    config = config.configuration
    artifact_config = AttrDict(
        use_wandb           = config.wandb.use,
        wandb_group         = config.wandb.group,
        wandb_entity        = config.wandb.entity,
        wandb_project       = config.wandb.project,
        train_artifact      = config.artifacts.train,
        valid_artifact      = config.artifacts.valid.data,
        # In case valid_artifact is None, this will set the percentage of random items to go to val
        valid_size          = config.artifacts.valid.size,
        w                   = config.specifications.sliding_windows.size,
        stride              = config.specifications.sliding_windows.stride,
        delta               = config.specifications.autoencoder.delta,
        nfs                 = config.specifications.autoencoder.filters.nfs,
        kss                 = config.specifications.autoencoder.filters.kss,
        output_filter_size  = config.specifications.autoencoder.filters.output_size,
        pool_szs            = config.specifications.pool_szs,
        batch_size          = config.specifications.batch_size, 
        epochs              = config.specifications.n_epoch,
        top_k               = config.specifications.pool_szs
    )
    check_project_and_entity(artifact_config.wandb_entity, artifact_config.wandb_project)
    return artifact_config, config.job_type


######################
# 03 - EMBEDDINGS    #
######################
def get_artifact_config_embeddings(print_flag=False):
    config = get_config(print_flag, "03-embeddings")
    job_type=config.job_type
    config = config.configuration
    artifact_config = AttrDict(
        use_wandb       = config.wandb.use,
        wandb_group     = config.wandb.group,
        wandb_entity    = config.wandb.entity,
        wandb_project   = config.wandb.project,
        enc_artifact    = config.artifacts.enc,
        input_ar        = config.specifications.input_ar,
        cpu             = config.specifications.cpu
    )
    check_project_and_entity(artifact_config.wandb_entity, artifact_config.wandb_project)
    return artifact_config, job_type


###################################
# 03 - DIMENSIONALITY REDUCTION   #
###################################
def get_artifact_config_dimensionality_reduction(print_flag=False):
    config          = get_config(print_flag, "04-dimensionality_reduction")
    job_type        = config.job_type
    config          = config.configuration
    artifact_config = AttrDict(
        use_wandb           = config.wandb.use, 
        wandb_group         = config.wandb.group,
        wandb_entity        = config.wandb.entity,
        wandb_project       = config.wandb.project,
        dr_artifact_name    = config.encoder.artifact.valid, 
        enc_artifact        = config.encoder.artifact.enc,
        n_neighbors         = config.encoder.umap.n_neighbors,
        min_dist            = config.encoder.umap.min_dist,
        random_state        = config.encoder.umap.random_state
    )
    return artifact_config, job_type