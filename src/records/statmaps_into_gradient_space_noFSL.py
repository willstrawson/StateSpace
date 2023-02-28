# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 08:17:21 2023

@author: bront

Script to correlate task maps with gradients WITHOUT using FSL

"""

import numpy as np
import nibabel as nib
from nilearn import image as nimg

import glob
from scipy.stats import spearmanr, pearsonr, zscore
#from nilearn.image import resample_to_img
import os 
import subprocess

import pandas as pd
import matplotlib.pyplot as plt 


def corrTasks(corr_method='spearman'):

    # get all the relevent data 
    gradient_paths, gradient_mask_path, task_paths, repo_path = getdata() # Get all the data paths you need
    # load mask as nib object once 
    maskimg = nib.load(gradient_mask_path)

    corr_dictionary = {}

    # loop over each task
    for task in task_paths:

        # load task image and data
        taskimg = nib.load(task)
        
        # extract task name from file path
        task_name = task.split(".")[0]
        task_name =  task_name.split("/")[-1]

        # apply mask 
        multmap = nimg.math_img('a*b',a=taskimg, b=maskimg) #element wise multiplication 

        nib.save(multmap, 
        os.path.join(repo_path,f'scratch/{task_name}_masked.nii.gz'))

        # turn to numpy array 
        task_array_masked = multmap.get_fdata()
                

        # create 1st level dictionary key (task name)
        corr_dictionary[task_name] = {}
        
        print (task_name)

        # Iterate through each of Neurovault's gradients
        for index, (gradient) in enumerate(gradient_paths):

            gradnumber = index+1 # set grad number based on index
            print (gradnumber)
            
            # load gradient
            gradientimg = nib.load(gradient)
                 
            # Get the gradient image data as a numpy array
            gradient_array = gradientimg.get_fdata()
            
            # correlate task map and gradients 
            if corr_method == 'spearman':
                corr = spearmanr(gradient_array.flatten(), task_array_masked.flatten())[0]

            elif corr_method == 'pearson':
                corr = pearsonr(gradient_array.flatten(), task_array_masked.flatten())[0]

            print('\n')
            
            # plot 
            #plt.scatter(gradient_array.flatten(), task_array_masked.flatten(), marker='.')
            #plt.savefig(os.path.join(repo_path,f'scratch/plots/{task_name}_{gradnumber}_scatter.png'))
            #plt.close()


            corr_dictionary[task_name][gradnumber]= corr # add corr value to dict
    
    df = pd.DataFrame(corr_dictionary).T
    df.to_csv(os.path.join(repo_path,f'scratch/gradscores_{corr_method}.tsv'),sep='\t')   
    return df

# Get path to repository
def getdata():
    repo_path = os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
    # path to cotical only gradient maps 
    gradient_paths = glob.glob(os.path.join(repo_path, 'data/gradients/*.nii.gz'))
    # mask from these cortical-only maps 
    gradient_mask_path = glob.glob(os.path.join(repo_path, 'data/masks/gradientmask_cortical.nii.gz'))[0]
    # task maps 
    task_paths = glob.glob(os.path.join(repo_path, 'data/realTaskNiftis/*.nii.gz'))

    return gradient_paths, gradient_mask_path, task_paths, repo_path


corrTasks()


