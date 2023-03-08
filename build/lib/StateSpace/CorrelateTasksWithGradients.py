# -*- coding: utf-8 -*-
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


# this function extracts necessary data needed to run corrTasks function (see below)
def getdata():
    # set path to current repository
    repo_path = os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
    # path to cotical only gradient maps 
    gradient_paths = sorted(glob.glob(os.path.join(repo_path, 'data/gradients/*.nii.gz')))
    # mask from these cortical-only maps 
    gradient_mask_path = glob.glob(os.path.join(repo_path, 'data/masks/gradientmask_cortical.nii.gz'))[0]
    # task maps 
    task_paths = sorted(glob.glob(os.path.join(repo_path, 'data/realTaskNiftis/*.nii.gz')))
    # return paths
    return gradient_paths, gradient_mask_path, task_paths, repo_path


# this function correlates task maps and gradient maps
def corrTasks(outputdir, corr_method='spearman', saveMaskedimgs = False):

    # get all the relevent data by calling getdata() function
    gradient_paths, gradient_mask_path, task_paths, repo_path = getdata() # Get all the data paths you need
    
    # load mask as nib object once 
    maskimg = nib.load(gradient_mask_path)

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
        multmap = nimg.math_img('a*b',a=taskimg, b=maskimg) #element wise multiplication 
        
        # if you want to save masked task images, set to true
        if saveMaskedimgs == True:
            nib.save(multmap, 
            os.path.join(outputdir,f'{task_name}_masked.nii.gz'))

        # turn to numpy array 
        task_array_masked = multmap.get_fdata()
                
        # create 1st level dictionary key (task name)
        corr_dictionary[task_name] = {}
        
        print (task_name)
        print('\n')

        # Iterate through each of Neurovault's gradients
        for index, (gradient) in enumerate(gradient_paths):

            grad_name = os.path.basename(os.path.normpath(gradient))
            grad_name = grad_name.split(".")[0]
            
            print (grad_name)
            
            # load gradient
            gradientimg = nib.load(gradient)
                 
            # Get the gradient image data as a numpy array
            gradient_array = gradientimg.get_fdata()
            
            # correlate task map and gradients 
            if corr_method == 'spearman':
                corr = spearmanr(gradient_array.flatten(), task_array_masked.flatten())[0]

            elif corr_method == 'pearson':
                corr = pearsonr(gradient_array.flatten(), task_array_masked.flatten())[0]
                
            print ("Raw correlation:",corr)
                
            # apply fishers-r-to-z transformation to correlation value
            corr = np.arctanh(corr)
            
            print ("Fisher r-to-z transformed correlation:",corr)

            # plot correlation of flattened arrays [mostly for testing but keeping for now]
            #plt.scatter(gradient_array.flatten(), task_array_masked.flatten(), marker='.')
            #plt.savefig(os.path.join(repo_path,f'scratch/plots/{task_name}_{gradnumber}_scatter.png'))
            #plt.close()

            corr_dictionary[task_name][grad_name]= corr # add corr value to dict
    
    # store results in transposed dataframe
    df = pd.DataFrame(corr_dictionary).T
    df.index.name = 'Task_name'
    # save dataframe to csv
    df.to_csv(os.path.join(outputdir,f'gradscores_{corr_method}.tsv'),sep='\t')
    
    return df




