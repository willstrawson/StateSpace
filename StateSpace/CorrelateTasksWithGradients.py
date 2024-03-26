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
from scipy.stats import zscore

def get_sorted_paths(subdir, pattern):
    """
    Returns sorted paths (used by getdata)
    """
    subdir_path = pkg_resources.resource_filename('StateSpace', subdir)
    return sorted(glob.glob(f'{subdir_path}/{pattern}'))

def getdata(mask_name, map_coverage):
    """
    Get the paths of gradient, mask, and task files.

    Args:
        mask_name (str): The name of the mask.
        map_coverage (str): The coverage of the map.

    Returns:
        tuple: A tuple containing the paths of gradient files, mask file, and task files stored in data/realTaskNiftis.
    """

    # read in gradient path, dependent on map_coverage argument (cortical_only or cortical-subcortical)
    gradient_pattern = '*cortical_only.nii.gz' if map_coverage == 'cortical_only' else '*subcortical.nii.gz'
    gradient_paths = get_sorted_paths('data/gradients', gradient_pattern)

    # first, try to read mask_name from data/masks
    try: 
        mask_paths = get_sorted_paths('data/masks', f'{mask_name}.nii.gz')
        mask_path = mask_paths[0]
    # otherwise, looks everywhere for path
    except:
        if os.path.exists(mask_name):
            mask_path = f'{mask_name}'
        else:
            print ("Mask path not found. If using own mask, provide full path.")

    # as default, returns 14-task task battery baths (in future, would like to change)
    task_paths = get_sorted_paths('data/realTaskNiftis', '*nii.gz')

    return gradient_paths, mask_path, task_paths

def usrpaths(inputfiles, verbose, mask_name, map_coverage):
    assert type(inputfiles)==list 
    assert os.path.exists(os.path.dirname(inputfiles[0]))
    if verbose > 0:
        print(f"Using {len(inputfiles)} input task maps")
    gradient_paths, mask_path, task_paths = getdata(mask_name, map_coverage)
    task_paths = inputfiles
    return  gradient_paths, mask_path, task_paths

def applymask(img, maskimg):
    """
    Return masked image.

    Args:
        img (nibabel image object): Image to apply mask to.
        maskimg (nibabel image object): Mask image to apply to image.

    Returns:
        Masked img.
    """
    # try to apply without reshaping
    try:
        return nimg.math_img('a*b',a=img, b=maskimg) #element wise multiplication - return the resulting map
    # if shapes don't match, reshape img
    except ValueError: 
        print('Shapes of images do not match')
        print(f'mask-image shape: {maskimg.shape}, image shape {img.shape}')
        print('Reshaping image to mask-image dimensions...')
        img = nimg.resample_to_img(source_img=img,target_img=maskimg,interpolation='nearest')
        return nimg.math_img('a*b',a=img, b=maskimg) #element wise multiplication - return the resulting map
    
def gradname(gradient_path, verbose):
    grad_name = os.path.basename(os.path.normpath(gradient_path))
    grad_name = grad_name.split(".")[0]
    if verbose > 0:
        print (grad_name)
    return grad_name

def corrGrads(gradient_array, input_array, corr_method='spearman', verbose=1):
    """
    Correlate input array with gradient array.

    Args:
        gradient_array (numpy array): Gradient array.
        input_array (numpy array): Input array to correlate with gradient array.
        corr_method (str, optional): String indicating which correlation method. Defaults to spearman.
        verbose (int, optional): The verbosity level. Defaults to 1.

    Returns:
        corr (float): Correlation value.
    """
    if corr_method == 'spearman':
        corr = spearmanr(gradient_array.flatten(), input_array.flatten())[0]
        if verbose > 0:
            print (f"Spearman correlation:",corr)

    elif corr_method == 'pearson':
        corr = pearsonr(gradient_array.flatten(), input_array.flatten())[0]
		# apply fishers-r-to-z transformation to correlation value
        corr = np.arctanh(corr)
        if verbose > 0:
            print (f"Pearson (Fisher r-to-z) correlation:",corr)
    return corr

def corrGroup(mask_name, map_coverage, outputdir=None, inputfiles=None,
              corr_method='spearman', saveMaskedimgs = False,verbose=1):
    """
    Calculate the correlation between task maps and gradients.

    Args:
        mask_name (str): The name of the mask.
        map_coverage (str): The coverage of the map.
        outputdir (str, optional): The output directory. Defaults to None.
        inputfiles (list, optional): The input task maps. Defaults to None.
        corr_method (str, optional): The correlation method. Defaults to 'spearman'.
        saveMaskedimgs (bool, optional): Whether to save masked task images. Defaults to False.
        verbose (int, optional): The verbosity level. Defaults to 1.

    Returns:
        pandas.DataFrame: The correlation values between task maps and gradients.
    """
    # get all the relevent data by calling getdata() function
    # if inputfiles not provided, will use 14 task battery maps in data/realTaskNiftis
    if inputfiles is None:
        gradient_paths, mask_path, task_paths = getdata(mask_name, map_coverage) 
    # if inputfiles provided, will use those
    elif inputfiles:
        gradient_paths, mask_path, task_paths = usrpaths(inputfiles, verbose, mask_name, map_coverage)

    # create empty dictionary to store correlation values in
    corr_dictionary = {}

    # load maskimg once before loops
    maskimg=nib.load(mask_path)

    # loop over each task_path in task_paths
    for task in task_paths:

        # extract task name from file path
        task_name = os.path.basename(os.path.normpath(task))
        task_name = task_name.split(".")[0]

        # load taskimg
        taskimg=nib.load(task)

        # apply mask to taskimg
        multmap = applymask(taskimg, maskimg)

        # turn maskim to numpy array
        task_array_masked = multmap.get_fdata()

        # if you want to save masked task images in outputdir, set to true
        if saveMaskedimgs == True and outputdir != None:
            nib.save(multmap, 
            os.path.join(outputdir,f'{task_name}_masked.nii.gz'))

        # create 1st level dictionary key (task name)
        corr_dictionary[task_name] = {}
        if verbose > 0:
            print (task_name)
            print('\n')

        # Iterate through each of Neurovault's gradients
        for gradient in gradient_paths:

            # extract grad name from file path
            grad_name = gradname(gradient, verbose)

            # load gradient image and apply mask
            gradient_img=nib.load(gradient)
            gradientimg_m = applymask(gradient_img, maskimg) 

            # Get the masked gradient image data as a numpy array
            gradient_array_masked = gradientimg_m.get_fdata()

            # call corrGrads to return corr
            corr = corrGrads(gradient_array_masked,task_array_masked)

            # add corr value to dict
            corr_dictionary[task_name][grad_name] = corr 

    # store results in transposed dataframe
    df = pd.DataFrame(corr_dictionary).T
    df.index.name = 'Task_name' # set index name to Task_name

    # save dataframe to csv if outputdir provided
    if outputdir != None:
        df.to_csv(os.path.join(outputdir,f'gradscores_{corr_method}_{mask_name}.csv'))

    return df

def extractid(pth, string):
    """
    Extracts the ID from a file path.
    Note: assumes BIDS format where each 'sub', 'task' and 'run' stored in own folders.

    Args:
        pth (str): The file path.
        runstring (str): The string identifying the sub / task / run.

    Returns:
        str: The ID extracted from the file path.
    """

    # Normalize the path using os.path
    normalized_path = os.path.normpath(pth)
    
    # split path using forward slash
    splits = normalized_path.split(os.path.sep)

    id = [i for i in splits if string in i]
    
    assert id

    return id[0]

def corrInd(mask_name, map_coverage, inputfiles,
            taskstring, substring, runstring = None,
            outputdir = None,
            corr_method='spearman', verbose=1):
    """
    Correlate individual-level maps and gradient maps.

    Args:
        mask_name (str): The name of the mask.
        map_coverage (str): The coverage of the map.
        inputfiles (list): The input task map filepaths.
        taskstring (str): The string identifying the task (assumes BID format).
        substring (str): The string identifying the subject (assumes BID format).

        runstring (str, optional): The string identifying the run (assumes BID format). Defaults to None.
        outputdir (str, optional): The output directory. Defaults to None.
        corr_method (str, optional): The correlation method. Defaults to 'spearman'.
        verbose (int, optional): The verbosity level. Defaults to 1.

    Returns:
        pandas.DataFrame: The correlation values between task maps and gradients.
    """
    #  retrieve file paths
    gradient_paths, mask_path, task_paths = usrpaths(inputfiles, verbose, mask_name, map_coverage)

    # load mask as nib object once 
    maskimg = nib.load(mask_path) 

    # create empty dictionary to store correlation values in
    corr_dictionary = {}

    # loop over each task
    for task in task_paths:

        # extract task name and subject id from file path
        task_name = extractid(task, taskstring)
        subid = extractid(task, substring)

        # load task image and apply mask
        taskimg = nib.load(task)
        multmap = applymask(taskimg, maskimg)

        # turn to numpy array
        task_array_masked = multmap.get_fdata()

        # create the 1st level dictionary key (task name)
        if task_name not in corr_dictionary:
            corr_dictionary[task_name] = {}

        # create the 2nd level dictionary key (subject id) if it doesn't exist
        if subid not in corr_dictionary[task_name]:
            corr_dictionary[task_name][subid] = {}

        # if runstring provided, add level to dict
        if runstring is not None:
            runid_val = extractid(task, runstring)
            # create the 3rd level dictionary key (runid) if it doesn't exist
            if runid_val not in corr_dictionary[task_name][subid]:
                corr_dictionary[task_name][subid][runid_val] = {}

        if verbose > 0:
            print (task_name)
            print('\n')

        # Iterate through each of Neurovault's gradients
        for gradient in gradient_paths:
            # retrieve gradname
            grad_name = gradname(gradient, verbose)

            # load gradient image and apply mask
            gradientimg = nib.load(gradient)
            gradientimg_m = applymask(gradientimg, maskimg)  

            # Get the masked gradient image data as a numpy array
            gradient_array_masked = gradientimg_m.get_fdata()

            # correlate masked task map and gradients 
            corr = corrGrads(gradient_array_masked,task_array_masked)

            # add to corr dictionary
            if runstring is None:
                corr_dictionary[task_name][subid][grad_name] = corr
            else:
                corr_dictionary[task_name][subid][runid_val][grad_name] = corr

    # if runstring not provided
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
    
    # if runstring is provided
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
 
    # save dataframe to csv if output directory provided
    if outputdir != None:
        df_long.to_csv(os.path.join(outputdir,f'gradscores_{corr_method}_{mask_name}_long.csv'), index=False)
        df_wide.to_csv(os.path.join(outputdir,f'gradscores_{corr_method}_{mask_name}_wide.csv'), index=False)

    return df_wide

def mask4d(img, maskimg):
# reshape mask to be 4d (additional dimension of time)
    print ("original mask shape:",maskimg.get_fdata().shape)
    mask_reshaped = np.expand_dims(maskimg.get_fdata(), axis=-1)
    img_shape = img.shape
    mask_reshaped = np.tile(mask_reshaped, (1, 1, 1, img_shape[3]))
    print ("mask reshaped:",mask_reshaped.shape)
    # convert 4-d mask back to image
    return nib.Nifti1Image(mask_reshaped, maskimg.affine)

def calGroupTimeCourse(mask_name, map_coverage, inputfiles, z_score = True, verbose=1):
    """
    Calculate group-averaged time course for per TR function.

    Args:
        mask_name (str): The name of the mask.
        map_coverage (str): The coverage of the map.
        inputfiles (list): The input task map filepaths.

        z_score (boolean, optional): Whether to z-score ind data prior to averaging. Defaults to True.
        verbose (int, optional): The verbosity level. Defaults to 1.

    Returns:
        numpy array: The masked group-averaged time course as a 4-d numpy array.
    """
    
    # get mask and task paths
    gradient_paths, mask_path, task_paths=usrpaths(inputfiles, verbose, mask_name, map_coverage)

    # load mask as nib object
    maskimg = nib.load(mask_path)

    # create empty list to store individual arrays
    data_arrays = []

    # load all data into a list of 4-d arrays
    for task in task_paths:
        taskimg = nib.load(task)
        taskarray = taskimg.get_fdata()
        # default behavior is to z-score each img
        if z_score:
            ztaskarray = zscore(taskarray, axis=None, ddof=1)
            data_arrays.append(ztaskarray)
        else:
            data_arrays.append(taskarray)

    # store affine of last input image for using below
    task_affine = taskimg.affine

    # Combine the individual arrays into a single 5D array (additional dimension for individuals)
    combined_brain_data = np.array(data_arrays)

    # Calculate the average along the first axis (axis=0) to get the average brain data across individuals
    # makes it a 4-day array again (group-average)
    group_averaged_time_course = np.mean(combined_brain_data, axis=0)

    # convert 4-d array back to nifi image using task_affine
    groupimg = nib.Nifti1Image(group_averaged_time_course, affine=task_affine)

    # make mask 4d
    maskimg_4d = mask4d(groupimg, maskimg)

    # apply 4-d mask to group-averaged image
    multmap=applymask(groupimg,maskimg_4d)

    # get data from masked array
    group_array_masked = multmap.get_fdata()

    return group_array_masked
    
def corrGroupTimeCourse(mask_name, map_coverage, group_array_masked, timecourse_name = None,outputdir=None,
              corr_method='spearman', verbose=1):
    
    """
    Calculate per TR correlations for group-averaged timecourse.

    Args:
        mask_name (str): The name of the mask.
        map_coverage (str): The coverage of the map.
        group_array_masked (numpy array): The group-averaged masked timecourse.

        timecourse_name (str, optional): Name of timecourse for saving results. Defaults to None.
        outputdir (str, optional): The output directory. Defaults to None.
        corr_method (str, optional): The correlation method. Defaults to 'spearman'.
        verbose (int, optional): The verbosity level. Defaults to 1.

    Returns:
        pandas.DataFrame: The correlation values for each TR.
    """
    
    # get gradiet and mask paths
    gradient_paths, mask_path, task_paths = getdata(mask_name, map_coverage)
    
    # load mask image once
    maskimg = nib.load(mask_path)

    # create corr dictionary for results
    corr_dictionary = {}

    # Iterate through each of Neurovault's gradients
    for gradient in gradient_paths:

        # retrieve gradname
        grad_name = gradname(gradient, verbose)

        # create key for gradient
        if grad_name not in corr_dictionary:
            corr_dictionary[grad_name] = {}

        # load gradient image and apply mask
        gradientimg = nib.load(gradient)
        gradientimg_m = applymask(gradientimg, maskimg)               

        # Get the masked gradient image data as a numpy array
        gradient_array = gradientimg_m.get_fdata()

        # loop over group-averaged array TRs (4th dimension)
        for tr_volume in range(group_array_masked.shape[3]):

            # select TR volume
            tr_array_masked = group_array_masked[:, :, :, tr_volume]

            # correlate task map and gradients
            corr = corrGrads(gradient_array, tr_array_masked)

            if verbose > 0:
                print ("TR:",tr_volume)

            # add to dict
            corr_dictionary[grad_name][tr_volume] = corr

    # Transform corr_dictionary into pandas DataFrame
    df = pd.DataFrame({grad_name: [corr_dictionary[grad_name].get(tr_volume, None) for tr_volume in corr_dictionary.get(grad_name, {})] for grad_name in corr_dictionary})
    
    # Set the index name to 'TR'
    df.index.name = 'TR'

    # save to output dir
    if outputdir != None:
        df.to_csv(os.path.join(outputdir,f'gradscores_grp_{timecourse_name}_{corr_method}_{mask_name}.csv'))

    return df

def corrIndTimeCourse(mask_name, map_coverage, inputfiles, substring, timecourse_name = None, outputdir=None,
              corr_method='spearman', verbose=1):
    
    """
    Calculate per TR correlations for individual level timecourses.

    Args:
        mask_name (str): The name of the mask.
        map_coverage (str): The coverage of the map.
        inputfiles (list): List of filepaths. All nifti files must have same number of volumes.
        substring (str): The string for finding subid in filepath. Assumes BID format.

        timecourse_name (str, optional): Name of timecourse for saving results. Defaults to None.
        outputdir (str, optional): The output directory. Defaults to None.
        corr_method (str, optional): The correlation method. Defaults to 'spearman'.
        verbose (int, optional): The verbosity level. Defaults to 1.

    Returns:
        pandas.DataFrame: The correlation values for each person and each TR.
    """
    
    # get paths
    gradient_paths, mask_path, task_paths = usrpaths(inputfiles, verbose, mask_name, map_coverage)
    
    # load mask image once
    maskimg = nib.load(mask_path)

    # create empty dictionary to store correlation values in
    corr_dictionary = {}

    # loop over indiviudal file paths
    for ind_path in task_paths:
        # extract subject id from file path
        subid = extractid(ind_path, substring)

        # load ind image
        indimg = nib.load(ind_path)

        # make mask 4d (TO DO: change this because this means 4d mask is made for each person)
        maskimg_4d = mask4d(indimg, maskimg)

        # apply mask
        multmap = applymask(indimg, maskimg_4d)

        # turn to numpy array
        ind_array_masked = multmap.get_fdata()

        # create the 1st level dictionary key (sub id)
        if subid not in corr_dictionary:
            corr_dictionary[subid] = {}

        # Iterate through each of Neurovault's gradients
        for gradient in gradient_paths:
            # retrieve gradname
            grad_name = gradname(gradient, verbose)

            # load gradient image and apply mask
            # create key for gradient
            if grad_name not in corr_dictionary:
                corr_dictionary[subid][grad_name] = {}

            # load gradient image and apply mask
            gradientimg = nib.load(gradient)
            gradientimg_m = applymask(gradientimg, maskimg)               

            # Get the masked gradient image data as a numpy array
            gradient_array = gradientimg_m.get_fdata()

            # loop over group-averaged array TRs (4th dimension)
            for tr_volume in range(ind_array_masked.shape[3]):

                # select TR volume
                tr_array_masked = ind_array_masked[:, :, :, tr_volume]

                # correlate task map and gradients
                corr = corrGrads(gradient_array, tr_array_masked)

                if verbose > 0:
                    print ("subid",subid,"TR:",tr_volume)

                # add to dict
                corr_dictionary[subid][grad_name][tr_volume] = corr

    # Create an empty list to store data in long format
    data_long = []

    # Iterate through the nested dictionary to convert it to long format
    for subid, grad_dict in corr_dictionary.items():
        for grad, tr_dict in grad_dict.items():
            data_long.extend([subid, grad, TR, corr] for TR, corr in tr_dict.items())

    # Create the 'df_long' DataFrame
    df_long = pd.DataFrame(data_long, columns=['subid', 'Gradient', 'TR', 'Correlation'])

    # Create the 'df_wide' DataFrame
    df_wide = df_long.pivot_table(index=['subid', 'TR'], columns='Gradient', values='Correlation').reset_index()

    # save to output dir
    if outputdir != None:
        df_wide.to_csv(os.path.join(outputdir,f'gradscores_ind_{timecourse_name}_{corr_method}_{mask_name}.csv'), index = False)

    return df_wide
