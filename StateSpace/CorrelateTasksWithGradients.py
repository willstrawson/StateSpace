# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
Created on Wed Feb 22 08:17:21 2023

@author: bront

Contains functions to correlate tasks in task battery with gradients.

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


# this function extracts necessary data needed to run corrTasks function (see below)
def getdata(data, mask_name):
    if data == 'gradients':
        # use pkg_resources to access the absolute path for each data subdirectory 
        canonical_paths = pkg_resources.resource_filename('StateSpace','data/gradients')

    elif data == 'pain': # if working with cannonical pain maps (not gradients)
    # NOTE: map_covarage not operationaized here as i've only made the one vps map
    # TODO: Create cortical only version of vps map and nname the two accordingly 
        # use pkg_resources to access the absolute path for each data subdirectory 
        pain_subdir = pkg_resources.resource_filename('StateSpace','data/pain')
        # then use glob to access a list of files within
        canonical_paths = sorted(glob.glob(f'{pain_subdir}/*.nii.gz'))

    mask_subdir = pkg_resources.resource_filename('StateSpace','data/masks')
    mask_path = sorted(glob.glob(f'{mask_subdir}/{mask_name}.nii.gz'))[0]



    task_subdir = pkg_resources.resource_filename('StateSpace','data/realTaskNiftis')
    task_paths = sorted(glob.glob(f'{task_subdir}/*nii.gz'))

    return canonical_paths, mask_path, task_paths

# this function correlates group maps and gradient maps
def corrGroup(mask_name, map_coverage, outputdir=None, inputfiles=None,
              corr_method='spearman', saveMaskedimgs = False,verbose=-1):

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
    Function to extract task id and sub id from file path if running individual level analyses
 
    """
    splits = pth.split('/')

    taskid = [i for i in splits if taskstring in i]
    subid = [i for i in splits if substring in i]

    assert taskid
    assert subid

    return taskid[0], subid[0]

def taskid_subid_pain(pth, taskstring, substring):
    """
    Function to extract task id and sub id from file path if running individual level analyses
    This is a custom function for the pain dataset, where taskid and subid are in the filename
 
    """
    picture_contrast_dict = {
        '00001': 'foot_nopain',
        '00002': 'foot_pain',
        '00003': 'hand_nopain',
        '00004': 'hand_pain',
        '00005': 'foot_nopain_fix',
        '00006': 'foot_pain_fix',
        '00007': 'hand_nopain_fix',
        '00008': 'hand_pain_fix'
    }
    video_contrast_dict = {
        '00001':'cue_self1hand',
        '00002':'cue_other1hand',
        '00003':'cue_self2hand',
        '00004':'cue_other2hand',
        '00005':'cue_self3hand',
        '00006':'cue_other3hand',
        '00007':'cue_self1foot',
        '00008':'cue_other1foot',
        '00009':'cue_self2foot',
        '00010':'cue_other2foot',
        '00011':'cue_self3foot',
        '00012':'cue_other3foot',
        '00013':'shock_self1hand',
        '00014':'shock_other1hand',
        '00015':'shock_self2hand',
        '00016':'shock_other2hand',
        '00017':'shock_self3hand',
        '00018':'shock_other3hand',
        '00019':'shock_self1foot',
        '00020':'shock_other1foot',
        '00021':'shock_self2foot',
        '00022':'shock_other2foot',
        '00023':'shock_self3foot',
        '00024':'shock_other3foot',
        '00025':'circle_self1hand',
        '00026':'circle_other1hand',
        '00027':'circle_self2hand',
        '00028':'circle_other2hand',
        '00029':'circle_self3hand',
        '00030':'circle_other3hand',
        '00031':'circle_self1foot',
        '00032':'circle_other1foot',
        '00033':'circle_self2foot',
        '00034':'circle_other2foot',
        '00035':'circle_self3foot',
        '00036':'circle_other3foot',
    }
    
    splits = os.path.split(pth)[-1].split('_')

    taskid = [i for i in splits if taskstring in i]
    subid = [i for i in splits if substring in i]

    if 'picture' in splits:
        taskid = [v for k,v in picture_contrast_dict.items() if k == taskid[0].strip('.nii')]

    if 'video' in splits:
        taskid = [v for k,v in video_contrast_dict.items() if k == taskid[0].strip('.nii')]

 
    print(splits)
    assert taskid[0]
    assert subid[0]

    return taskid[0], subid[0]

def runid(pth, runstring):
    """
    Function to extract run id from file path if running run level analyses
    """
    splits = pth.split('/') 

    runid = [i for i in splits if runstring in i]
    
    assert runid

    return runid[0]

# this function correlates individual-level maps and gradient maps
def corrInd(
    data, 
    sim_metric, 
    mask_name, 
    inputfiles, 
    outputdir,
    taskstring, 
    substring, 
    runstring = None,
    verbose=1):

    assert type(inputfiles)==list
    assert os.path.exists(os.path.dirname(inputfiles[0]))
    if verbose > 0:
            print(f"Using {len(inputfiles)} input task maps")
    gradient_paths, mask_path, task_paths = getdata(data, mask_name)

    task_paths = inputfiles

    # load mask as nib object once 
    maskimg = nib.load(mask_path)

    # create empty dictionary to store correlation values in
    sim_dictionary = {}

    # loop over each task
    for task in task_paths:

        # load task image and data
        taskimg = nib.load(task)

        # extract task name and subject id from file path
        task_name, subid = taskid_subid_pain(task, taskstring, substring)

        # apply mask 
        try:
            multmap = nimg.math_img('a*b',a=taskimg, b=maskimg) #element wise multiplication 
        except ValueError: # if shapes don't match
            print('Shapes of images do not match')
            print(f'Mask image shape: {maskimg.shape}, Task image shape {taskimg.shape}')
            print('Reshaping task to mask image dimensions...')
            taskimg = nimg.resample_to_img(source_img=taskimg,target_img=maskimg,interpolation='nearest')
            multmap = nimg.math_img('a*b',a=taskimg, b=maskimg) #element wise multiplication

        # turn to numpy array
        task_array_masked = multmap.get_fdata()

        # create the 1st level dictionary key (task name)
        if task_name not in sim_dictionary:
            sim_dictionary[task_name] = {}

        # create the 2nd level dictionary key (subject id) if it doesn't exist
        if subid not in sim_dictionary[task_name]:
            sim_dictionary[task_name][subid] = {}

        if runstring is not None:
            runid_val = runid(task, runstring)
            # create the 3rd level dictionary key (runid) if it doesn't exist
            if runid_val not in sim_dictionary[task_name][subid]:
                sim_dictionary[task_name][subid][runid_val] = {}

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
            try:
                gradientimg_m = nimg.math_img('a*b',a=gradientimg, b=maskimg)

            except ValueError: # if shapes don't match
                print('Shapes of images do not match')
                print(f'Pain signature image shape: {gradientimg.shape}, mask image shape {maskimg.shape}')
                print('Reshaping task to mask image dimensions...')
                gradientimg = nimg.resample_to_img(source_img=gradientimg,target_img=maskimg,interpolation='nearest')
                gradientimg_m = nimg.math_img('a*b',a=gradientimg, b=maskimg) #element wise multiplication                

            # Get the gradient image data as a numpy array
            gradient_array = gradientimg_m.get_fdata()

            if sim_metric == 'corr':
                # correlate task map and gradients 
                corr = spearmanr(gradient_array.flatten(), task_array_masked.flatten())[0]
                if verbose > 0:
                    print ("Spearman correlation:",corr)
                
                sim = corr
            
            elif sim_metric == 'dotproduct':
                # perform dot product 
                assert gradient_array.shape == task_array_masked.shape
                dot = np.vdot(gradient_array,task_array_masked) # dot product but converts input arrays to 1-d vectors first

                sim = dot

            if runstring is None:
                sim_dictionary[task_name][subid][grad_name] = sim
            else:
                sim_dictionary[task_name][subid][runid_val][grad_name] = sim

    if runstring is None:
        # Create an empty list to store data in long format
        data_long = []

        # Iterate through the nested dictionary to convert it to long format
        for task, sub_dict in sim_dictionary.items():
            for sub, grad_dict in sub_dict.items():
                data_long.extend([task, sub, grad, sim] for grad, sim in grad_dict.items())
                
        # Create the 'df_long' DataFrame
        df_long = pd.DataFrame(data_long, columns=['Task_name', 'subid', 'Gradient', f'{sim_metric}'])

        # Create the 'df_wide' DataFrame
        df_wide = df_long.pivot_table(index=['Task_name', 'subid'], columns='Gradient', values=f'{sim_metric}').reset_index()

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
        for task_name, sub_dict in sim_dictionary.items():
            for sub_id, run_dict in sub_dict.items():
                process_dict(run_dict, task_name, sub_id)

        # Create the 'df_long' DataFrame
        df_long = pd.DataFrame(data_long, columns=['Task_name', 'subid', 'runid', 'Gradient', f'{sim_metric}'])

        # Create the 'df_wide' DataFrame
        df_wide = df_long.pivot_table(index=['Task_name', 'subid', 'runid'], columns='Gradient', values=f'{sim_metric}').reset_index()
 
    # save dataframe to csv
    if outputdir != None:
        df_long.to_csv(os.path.join(outputdir,f'{data}_{sim_metric}_{mask_name}_long.csv'), index=False)
        df_wide.to_csv(os.path.join(outputdir,f'{data}_{sim_metric}_{mask_name}_wide.csv'), index=False)

    return df_wide


