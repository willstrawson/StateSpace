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
def getdata(mask_name, map_coverage):
    # use pkg_resources to access the absolute path for each data subdirectory 
    gradient_subdir = pkg_resources.resource_filename('StateSpace','data/gradients')
    # then use glob to access a list of files within
    if map_coverage == 'cortical_only':
        gradient_paths = sorted(glob.glob(f'{gradient_subdir}/*cortical_only.nii.gz'))
    elif map_coverage == 'all':
        gradient_paths = sorted(glob.glob(f'{gradient_subdir}/*subcortical.nii.gz'))

    mask_subdir = pkg_resources.resource_filename('StateSpace','data/masks')
    mask_path = sorted(glob.glob(f'{mask_subdir}/{mask_name}.nii.gz'))[0]

    task_subdir = pkg_resources.resource_filename('StateSpace','data/realTaskNiftis')
    task_paths = sorted(glob.glob(f'{task_subdir}/*nii.gz'))

    return gradient_paths, mask_path, task_paths


# this function correlates task maps and gradient maps
def corrTasks(mask_name, map_coverage, outputdir=None, inputfiles=None,
              corr_method='spearman', saveMaskedimgs = False,verbose=-1,z_score=False):

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
                # corr = np.arctanh(corr)
                if verbose > 0:
                    print ("Pearson (Fisher r-to-z transformed) correlation:",corr)

            corr_dictionary[task_name][grad_name]= corr # add corr value to dict

    # store results in transposed dataframe
    df = pd.DataFrame(corr_dictionary).T
    df.index.name = 'Task_name'
    zsc_df = pd.DataFrame()
    if z_score:
        # Z-score each column and create new columns with the suffix '_z'
        for col in df.columns:
            zsc_df[f'Z{col}'] = zscore(df[col])
        if outputdir != None:
            zsc_df.to_csv(os.path.join(outputdir,f'Zgradscores_{corr_method}_{mask_name}.csv'))
        return zsc_df

    # save dataframe to csv
    if outputdir != None:
        df.to_csv(os.path.join(outputdir,f'gradscores_{corr_method}_{mask_name}.csv'))

    return df


