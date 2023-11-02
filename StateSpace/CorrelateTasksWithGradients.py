# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Created on Wed Feb 22 08:17:21 2023

@authors: Bronte Mckeown, Will Strawson, Ian Goodall-Halliwell

Contains functions to correlate:
1) group-level brain maps
2) individual-level brain maps
3) Per-TR brain maps

With the first five Gradients from Margulies et al.

This produces 'coordinates' in state space.

"""

import nibabel as nib
from nilearn import image as nimg
import glob
from scipy.stats import spearmanr, pearsonr
import os 
import pandas as pd
import numpy as np
import pkg_resources

def getdata(mask_name, map_coverage):
    """
    Get the paths of gradient, mask, and task files.

    Args:
        mask_name (str): The name of the mask.
        map_coverage (str): The coverage of the map.

    Returns:
        tuple: A tuple containing the paths of gradient files, mask file, and task files.
    """
    def get_sorted_paths(subdir, pattern):
        subdir_path = pkg_resources.resource_filename('StateSpace', subdir)
        return sorted(glob.glob(f'{subdir_path}/{pattern}'))

    gradient_pattern = '*cortical_only.nii.gz' if map_coverage == 'cortical_only' else '*subcortical.nii.gz'
    gradient_paths = get_sorted_paths('data/gradients', gradient_pattern)

    mask_paths = get_sorted_paths('data/masks', f'{mask_name}.nii.gz')
    mask_path = mask_paths[0]

    task_paths = get_sorted_paths('data/realTaskNiftis', '*nii.gz')

    return gradient_paths, mask_path, task_paths

def corrGroup(mask_name, map_coverage, outputdir=None, inputfiles=None,
              corr_method='spearman', saveMaskedimgs = False,verbose=-1):
    """
    Calculate the correlation between task maps and gradients.

    Args:
        mask_name (str): The name of the mask.
        map_coverage (float): The coverage of the map.
        outputdir (str, optional): The output directory. Defaults to None.
        inputfiles (list, optional): The input task maps. Defaults to None.
        corr_method (str, optional): The correlation method. Defaults to 'spearman'.
        saveMaskedimgs (bool, optional): Whether to save masked task images. Defaults to False.
        verbose (int, optional): The verbosity level. Defaults to -1.

    Returns:
        pandas.DataFrame: The correlation values between task maps and gradients.
    """

    # get all the relevent data by calling getdata() function
    if inputfiles is None:
        # Get all the data paths you need
        gradient_paths, mask_path, task_paths = getdata(mask_name, map_coverage) 
    elif inputfiles:
        assert type(inputfiles)==list 
        assert os.path.exists(os.path.dirname(inputfiles[0]))
        if verbose > 0:
            print(f"Using {len(inputfiles)} input task maps")
        gradient_paths, mask_path, task_paths = getdata(mask_name, map_coverage)
        task_paths = inputfiles

    # load mask as nib object once 
    maskimg = nib.load(mask_path)

    # create empty dictionary to store correlation values in
    corr_dictionary = {}

    # loop over each task
    for task in task_paths:

        # load task image and data
        taskimg = nib.load(task)

        # extract task name from file path
        task_name = os.path.basename(os.path.normpath(task))
        task_name = task_name.split(".")[0]

        # apply mask 
        try:
            multmap = nimg.math_img('a*b',a=taskimg, b=maskimg) #element wise multiplication 
        except ValueError: # if shapes don't match
            print('Shapes of images do not match')
            print(f'mask image shape: {maskimg.shape}, task image shape {taskimg.shape}')
            print('Reshaping task to mask image dimensions...')
            taskimg = nimg.resample_to_img(source_img=taskimg,target_img=maskimg,interpolation='nearest')
            multmap = nimg.math_img('a*b',a=taskimg, b=maskimg) #element wise multiplication 

        # if you want to save masked task images, set to true
        if saveMaskedimgs == True and outputdir != None:
            nib.save(multmap, 
            os.path.join(outputdir,f'{task_name}_masked.nii.gz'))

        # turn to numpy array 
        task_array_masked = multmap.get_fdata()

        # create 1st level dictionary key (task name)
        corr_dictionary[task_name] = {}
        if verbose > 0:
            print (task_name)
            print('\n')

        # Iterate through each of Neurovault's gradients
        for index, (gradient) in enumerate(gradient_paths):

            grad_name = os.path.basename(os.path.normpath(gradient))
            grad_name = grad_name.split(".")[0]
            if verbose > 0:
                print (grad_name)

            # load gradient
            gradientimg = nib.load(gradient)

            # apply mask to gradient
            gradientimg_m = nimg.math_img('a*b',a=gradientimg, b=maskimg)                

            # Get the gradient image data as a numpy array
            gradient_array = gradientimg_m.get_fdata()

            # correlate task map and gradients 
            if corr_method == 'spearman':
                corr = spearmanr(gradient_array.flatten(), task_array_masked.flatten())[0]
                if verbose > 0:
                    print ("Spearman correlation:",corr)

            elif corr_method == 'pearson':
                corr = pearsonr(gradient_array.flatten(), task_array_masked.flatten())[0]
		        # apply fishers-r-to-z transformation to correlation value
                corr = np.arctanh(corr)
                if verbose > 0:
                    print ("Pearson (Fisher r-to-z transformed) correlation:",corr)

            corr_dictionary[task_name][grad_name]= corr # add corr value to dict

    # store results in transposed dataframe
    df = pd.DataFrame(corr_dictionary).T
    df.index.name = 'Task_name'

    # save dataframe to csv
    if outputdir != None:
        df.to_csv(os.path.join(outputdir,f'gradscores_{corr_method}_{mask_name}.csv'))

    return df

def taskid_subid(pth, taskstring, substring):
    """
    Extracts the task ID and subject ID from a file path when running individual level analyses.

    Args:
        pth (str): The file path.
        taskstring (str): The string identifying the task.
        substring (str): The string identifying the subject.

    Returns:
        tuple: A tuple containing the task ID and subject ID extracted from the file path.
    """
    # Normalize the path using os.path
    normalized_path = os.path.normpath(pth)

    # split path using os.path.split
    splits = normalized_path.split(os.path.sep)

    taskid = None
    subid = None

    for i in splits:
        if taskstring in i:
            taskid = i
        if substring in i:
            subid = i
        if taskid and subid:
            break

    assert taskid
    assert subid

    return taskid, subid

def runid(pth, runstring):
    """
    Extracts the run ID from a file path when running run level analyses.

    Args:
        pth (str): The file path.
        runstring (str): The string identifying the run.

    Returns:
        str: The run ID extracted from the file path.
    """

    # Normalize the path using os.path
    normalized_path = os.path.normpath(pth)
    
    # split path using forward slash
    splits = normalized_path.split(os.path.sep)

    runid = [i for i in splits if runstring in i]
    
    assert runid

    return runid[0]

def corrInd(mask_name, map_coverage, inputfiles, outputdir,
            taskstring, substring, runstring = None,
            corr_method='spearman', verbose=-1):
    """
    Correlate individual-level maps and gradient maps.

    Args:
        mask_name (str): The name of the mask.
        map_coverage (float): The coverage of the map.
        inputfiles (list): The input task maps.
        outputdir (str): The output directory.
        taskstring (str): The string identifying the task.
        substring (str): The string identifying the subject.
        runstring (str, optional): The string identifying the run. Defaults to None.
        corr_method (str, optional): The correlation method. Defaults to 'spearman'.
        verbose (int, optional): The verbosity level. Defaults to -1.

    Returns:
        pandas.DataFrame: The correlation values between task maps and gradients.
    """


    assert type(inputfiles)==list
    assert os.path.exists(os.path.dirname(inputfiles[0]))
    if verbose > 0:
            print(f"Using {len(inputfiles)} input task maps")
    gradient_paths, mask_path, task_paths = getdata(mask_name, map_coverage)

    task_paths = inputfiles

    # load mask as nib object once 
    maskimg = nib.load(mask_path)

    # create empty dictionary to store correlation values in
    corr_dictionary = {}

    # loop over each task
    for task in task_paths:

        # load task image and data
        taskimg = nib.load(task)

        # extract task name and subject id from file path
        task_name, subid = taskid_subid(task, taskstring, substring)

        # apply mask 
        try:
            multmap = nimg.math_img('a*b',a=taskimg, b=maskimg) #element wise multiplication 
        except ValueError: # if shapes don't match
            print('Shapes of images do not match')
            print(f'mask image shape: {maskimg.shape}, task image shape {taskimg.shape}')
            print('Reshaping task to mask image dimensions...')
            taskimg = nimg.resample_to_img(source_img=taskimg,target_img=maskimg,interpolation='nearest')
            multmap = nimg.math_img('a*b',a=taskimg, b=maskimg) #element wise multiplication

        # turn to numpy array
        task_array_masked = multmap.get_fdata()

        # create the 1st level dictionary key (task name)
        if task_name not in corr_dictionary:
            corr_dictionary[task_name] = {}

        # create the 2nd level dictionary key (subject id) if it doesn't exist
        if subid not in corr_dictionary[task_name]:
            corr_dictionary[task_name][subid] = {}

        if runstring is not None:
            runid_val = runid(task, runstring)
            # create the 3rd level dictionary key (runid) if it doesn't exist
            if runid_val not in corr_dictionary[task_name][subid]:
                corr_dictionary[task_name][subid][runid_val] = {}

        if verbose > 0:
            print (task_name)
            print('\n')

        # Iterate through each of Neurovault's gradients
        for index, (gradient) in enumerate(gradient_paths):

            grad_name = os.path.basename(os.path.normpath(gradient))
            grad_name = grad_name.split(".")[0]
            if verbose > 0:
                print (grad_name)

            # load gradient
            gradientimg = nib.load(gradient)

            # apply mask to gradient
            gradientimg_m = nimg.math_img('a*b',a=gradientimg, b=maskimg)                

            # Get the gradient image data as a numpy array
            gradient_array = gradientimg_m.get_fdata()

            # correlate task map and gradients 
            if corr_method == 'spearman':
                corr = spearmanr(gradient_array.flatten(), task_array_masked.flatten())[0]
                if verbose > 0:
                    print ("Spearman correlation:",corr)

            elif corr_method == 'pearson':
                corr = pearsonr(gradient_array.flatten(), task_array_masked.flatten())[0]
		        # apply fishers-r-to-z transformation to correlation value
                corr = np.arctanh(corr)
                if verbose > 0:
                    print ("Pearson (Fisher r-to-z transformed) correlation:",corr)

            if runstring is None:
                corr_dictionary[task_name][subid][grad_name] = corr
            else:
                corr_dictionary[task_name][subid][runid_val][grad_name] = corr

    if runstring is None:
        # Create an empty list to store data in long format
        data_long = []

        # Iterate through the nested dictionary to convert it to long format
        for task, sub_dict in corr_dictionary.items():
            for sub, grad_dict in sub_dict.items():
                data_long.extend([task, sub, grad, corr] for grad, corr in grad_dict.items())
                
        # Create the 'df_long' DataFrame
        df_long = pd.DataFrame(data_long, columns=['Task_name', 'subid', 'Gradient', 'Correlation'])

        # Create the 'df_wide' DataFrame
        df_wide = df_long.pivot_table(index=['Task_name', 'subid'], columns='Gradient', values='Correlation').reset_index()

    else:
        # Create an empty list to store data in long format
        data_long = []

        # Function to recursively traverse the dictionary and create long format data
        def process_dict(d, task_name, sub_id, run_id=None):
            if isinstance(d, dict):
                for key, value in d.items():
                    if run_id is not None:
                        data_long.append([task_name, sub_id, run_id, key, value])
                    elif isinstance(value, dict):
                        process_dict(value, task_name, sub_id, key)
            else:
                return

        # Iterate through the nested dictionary to convert it to long format
        for task_name, sub_dict in corr_dictionary.items():
            for sub_id, run_dict in sub_dict.items():
                process_dict(run_dict, task_name, sub_id)

        # Create the 'df_long' DataFrame
        df_long = pd.DataFrame(data_long, columns=['Task_name', 'subid', 'runid', 'Gradient', 'Correlation'])

        # Create the 'df_wide' DataFrame
        df_wide = df_long.pivot_table(index=['Task_name', 'subid', 'runid'], columns='Gradient', values='Correlation').reset_index()
 
    # save dataframe to csv
    if outputdir != None:
        df_long.to_csv(os.path.join(outputdir,f'gradscores_{corr_method}_{mask_name}_long.csv'), index=False)
        df_wide.to_csv(os.path.join(outputdir,f'gradscores_{corr_method}_{mask_name}_wide.csv'), index=False)

    return df_wide








