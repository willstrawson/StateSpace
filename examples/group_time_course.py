'''
Correlate task maps with Gradients to produce state-space coordinates.

'''
import os
import re
import glob 
import nibabel as nib
import numpy as np
from StateSpace import CorrelateTasksWithGradients

def get_start_number(file_paths):
    start_numbers = []

    for file_path in file_paths:
        match = re.search(r'_run-(\d+)_', file_path)
        if match:
            current_number = int(match.group(1))
            start_numbers.append(current_number)

    return min(start_numbers)

def rename_files(file_paths, start_number):
    for file_path in file_paths:
        match = re.search(r'_run-(\d+)_', file_path)
        if match:
            current_number = int(match.group(1))
            new_number = current_number - start_number + 1
            new_file_path = re.sub(r'_run-\d+_', f'_run-{new_number}_', file_path)
            os.rename(file_path, new_file_path)

# Specify the parent folder containing participant folders
parent_folder = 'C:\\Users\\bront\\Downloads\\derivatives\\'

# Specify the pattern for participant folders
participant_pattern = 'sub-CN*'

# Specify the file pattern within each participant folder
file_pattern = 'func\\sub-CN*_task-lppCN_run-*_space-MNIColin27_desc-preproc_bold.nii.gz'

# Get the list of participant folders
participant_folders = glob.glob(os.path.join(parent_folder, participant_pattern))

# Process files for each participant separately
for participant_folder in participant_folders:
    # Construct the full file pattern for the participant
    participant_file_pattern = os.path.join(participant_folder, file_pattern)
    
    # Use glob to get the list of file paths matching the participant's pattern
    participant_files = glob.glob(participant_file_pattern)
    
    # Determine the start number for the participant
    start_number = get_start_number(participant_files)
    
    # Rename the files for the participant
    rename_files(participant_files, start_number)

# now for analysis
# get path to output dir 
outputdir = os.path.join(os.path.split(os.path.split(os.path.realpath(__file__))[0])[0], 'Downloads\\TestResults')

# if os.path.exists(outputdir) == False: #If scratch doesn't exist 
#     os.mkdir(outputdir)

inputfiles3 = glob.glob('C:\\Users\\bront\\Downloads\\derivatives\\sub-CN*\\func\\sub-CN*_task-lppCN_run-3_space-MNIColin27_desc-preproc_bold.nii.gz')

CorrelateTasksWithGradients.corrGroupTimeCourse('gradientmask_cortical_subcortical',
                                                    'all',
                                                    f'run3CN',
                                                    inputfiles3, 
                                                    outputdir,
                                                    corr_method='spearman',
                                                    verbose=1)