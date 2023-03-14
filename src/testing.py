# %%
import os
import glob
import pandas as pd
import nibabel as nib
import numpy as np
import scipy.stats as stats
import random
# import seaborn as sns
# import matplotlib.pyplot as plt
# from nilearn import plotting

from StateSpace import CorrelateTasksWithGradients

from scipy.spatial.distance import euclidean

# %% Functions

def avgTask(esq_df):
    """
    Parameters
    ----------
    esq_df : Dataframe containing ESQ data

    Returns
    -------
    ESQ item averages per task in ESQ dataframe provided.

    """
    task_averages = esq_df.groupby("Task_name", as_index = True)[['Absorption_response', 'Other_response',
           'Problem_response', 'Words_response', 'Sounds_response',
           'Images_response', 'Past_response', 'Distracting_response',
           'Focus_response', 'Intrusive_response', 'Deliberate_response',
           'Detailed_response', 'Future_response', 'Emotion_response',
           'Self_response', 'Knowledge_response']].mean().T.reset_index()
    
    task_averages.rename(columns = {'index':'esq'}, inplace = True)
    
    return task_averages

# Set any functions
def correlate_cca(cca_df, task_averages):
    """
    Compute the Pearson correlation coefficients between the projected PCA items in CCA space
    and each task's item averages in the provided DataFrames.
    """
    corr_dict = {}
    for column in task_averages.iloc[:, 1:]:
        correl = stats.pearsonr(task_averages[column], cca_df.iloc[:, 0])
        corr_dict[column] = correl[0]
    return corr_dict

# %% Read in data

# Read in ESQ data
esq_path = "/mnt/c/users/bront/Documents/CanadaPostdoc/MegaProject/MegaProject/scratch/data/output_withGrads_leaveOneOut_rotation-on_ncomponents=[4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4].csv"
esq = pd.read_csv(esq_path)

# Read in CCA projected PCA data
cca_csvs = [sorted(glob.glob(f"/mnt/c/users/bront/Documents/CanadaPostdoc/MegaProject/MegaProject/scratch/results/cca/leaveOneOut/projectedWordClouds/leftOut*_cca{i}_component_loadings_for_wordclouds.csv")) for i in range(1, 4)]
cca_list = [[pd.read_csv(csv, header = None) for csv in cca_csvs[i]] for i in range(len(cca_csvs))]

# Read in CCA projected brain data
cca_nifti_dict = {}
cca_nifti_paths = sorted(glob.glob("/mnt/c/users/bront/Documents/CanadaPostdoc/MegaProject/MegaProject/scratch/results/cca/leaveOneOut/projectedBrainMaps/cca*_without_*.nii.gz"))
for cca_path in cca_nifti_paths:
    img = nib.load(cca_path)
    task_name = os.path.splitext(os.path.basename(cca_path))[0].split("_without_")[-1]
    task_name = task_name.replace('.nii', '')  # Remove '.nii' from task_name
    cca_num = int(os.path.basename(cca_path).split("_")[0][3:])
    if task_name not in cca_nifti_dict:
        cca_nifti_dict[task_name] = {}
    cca_nifti_dict[task_name][cca_num] = img


# %% Create first distributions of 'good' synthetic maps

# 1000 iterations, on each iteration:
# Select a subset of ESQ observations
# Generate synthetic maps per task [using task averages]
# Calculate gradient co-ordinates for these synthetic maps
# Calculate distance between real and synthetic for each task map; 
# end result = x1000 distances for each gradient and task to create distribution of ‘good’ synthetic maps

# define the number of iterations you want to loop through
num_iterations = 1

good_perm = {}

for i in range(num_iterations):
    index = i +1
    # randomly select half of the participants
    participants = esq['Id_number'].unique()
    random.shuffle(participants)
    num_participants = len(participants)
    half_participants = participants[:num_participants // 2]
    
    # select the subset of the dataframe that corresponds to the selected participants
    subset = esq[esq['Id_number'].isin(half_participants)]
    
    print (subset.shape)
    
    # calculate average per task in subsetted dataframe
    averages = avgTask(subset)
    
    # initialize empty dictionary for adding results to
    cca_corrs_dict = {}
    
    # iterate over each CCA dimension at a time to calculate correlations
    # between ESQ task averages and CCA-projected ESQ items
    for index, (cca_paths, cca_dfs) in enumerate(zip(cca_csvs,cca_list)):
        # index corresponds to CCA dimension number 1-3
        index = index + 1
        # Initialize an empty dictionary for this CCA dimension
        cca_dict = {}
        # Iterate over all 14 versions of CCA dimension X (one for each task left out)
        # Here, each series = PCA item loadings multiplied by CCA item loadings
        for cca_path, cca_df in zip(cca_paths, cca_dfs):
            # Get the task name from the filename
            # task name = task omited when calculating CCA
            task_name = cca_path.split("_")[1]
            # Compute the correlation coefficients between this task's ESQ averages and the CCA-projected ESQ item PCA loadings
            corr_dict = correlate_cca(cca_df, averages)
            # Update the nested dictionary for this CCA dimension and task
            cca_dict[task_name] = corr_dict
        # Update the outer dictionary for this CCA dimension
        cca_corrs_dict[index] = cca_dict
    
    ### make synthetic maps
    # create empty dictionary for storing results
    cca_results_dict = {}

    ## Multiplication: multiply each CCA dimension brain map with corresponding 
    # correlation value between task ESQ averages and CCA projected PCA data

    # Loop over each task in the cca_nifti_dict
    for task in cca_nifti_dict.keys():

        # Initialize an empty list to store the results for each CCA
        task_results = []
        
        # Loop over each CCA number (1-3)
        for cca in range(1, 4):
            
            # Get the nifti file path for this task and cca number
            img = cca_nifti_dict[task][cca]
            data = img.get_fdata()
            
            # Get the correlation value for this task, cca number, and task name
            corr = cca_corrs_dict[cca][task][task]
            
            # Multiply the CCA dimension brain map by the correlation value
            corr_data = data * corr
            
            # Append the results to the task_results list
            # will result in three brain maps for each task
            task_results.append(corr_data)
            
        cca_results_dict[task] = task_results # add 3 results to dictionary for summing below
        
    ## Sum: sum these brain maps to produce one synthetic brain map per task

    # create empty dict for storing CCA generated task maps
    cca_generated_dict = {}

    for key, value in cca_results_dict.items():
        numpy_list = value
        # sum values in numpy_list to calculate dot product
        cca_sum = np.sum(numpy_list, axis = 0)
        
        # save as nifti image
        cca_image = nib.Nifti1Image(cca_sum, img.affine, img.header)
        
        # add image to dictioary
        cca_generated_dict[key] = cca_image
        
    # need to correlate synthetic maps with gradients to produce gradient scores per task map
    gradscores = CorrelateTasksWithGradients.corrTasks("", inputfiles=None, corr_method='spearman', 
              saveScores=False, saveMaskedimgs=False, nifti_dict= cca_generated_dict)
     
    # add grad scores to dictionary where key = iteration number, value = gradscores
    good_perm[index] = gradscores

    
## calculate distance between each iterations' grad scores and real grad scores
real_gradscores = CorrelateTasksWithGradients.corrTasks("", inputfiles=None, corr_method='spearman', 
              saveScores=False, saveMaskedimgs=False, nifti_dict= None)

# loop over synthetic scores stored in good_perm_dist and calculate difference 
# between each synthetic score and each real score from real_gradscores
good_diff_dict = {}

for perm_num, df in good_perm.items():
    diff_df = abs(real_gradscores.subtract(df))
    # add distance array to dictionary
    good_diff_dict[perm_num] = diff_df


    

    

