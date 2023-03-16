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
import subprocess



# this function extracts necessary data needed to run corrTasks function (see below)
def getdata():
    # use pkg_resources to access the absolute path for each data subdirectory 
    gradient_subdir = pkg_resources.resource_filename('StateSpace','data/gradients')
    # then use glob to access a list of files within 
    gradient_paths = sorted(glob.glob(f'{gradient_subdir}/*nii.gz'))

    mask_subdir = pkg_resources.resource_filename('StateSpace','data/masks')
    gradient_mask_path = sorted(glob.glob(f'{mask_subdir}/*_cortical.nii.gz'))[0]

    task_subdir = pkg_resources.resource_filename('StateSpace','data/realTaskNiftis')
    task_paths = sorted(glob.glob(f'{task_subdir}/*nii.gz'))


    return gradient_paths, gradient_mask_path, task_paths



# this function correlates task maps and gradient maps
def corrTasks(
    outputdir, 
    inputfiles=None, 
    corr_method='spearman', 
    saveMaskedimgs = False, 
    GroupLevelMaps=True):

    # initialize empty lists to store values
    taskids = []
    gradientids = []
    correlations = [] 
    fcorrelations = []
    fslcc_correlations = []

    subids = []
    runids=[]


    # get all the relevent data by calling getdata() function
    if inputfiles is None:
        gradient_paths, gradient_mask_path, task_paths = getdata() # Get all the data paths you need

    elif inputfiles:
        assert type(inputfiles)==list 
        assert os.path.exists(os.path.dirname(inputfiles[0]))
        print(f"Using {len(inputfiles)} input task maps")
        gradient_paths, gradient_mask_path, task_paths = getdata()
        task_paths = inputfiles


    # load mask as nib object once 
    maskimg = nib.load(gradient_mask_path)

    # create empty dictionary to store correlation values in
    corr_dictionary = {}

    # loop over each task
    for task in task_paths:

        # TODO: If using maps from individual subjects (group level maps = False), extract subid and other important information

        # load task image and data
        taskimg = nib.load(task)

        # extract task name from file path
        task_name = os.path.basename(os.path.normpath(task))
        task_name = task_name.split(".")[0]

        if GroupLevelMaps==False:
            subid, runid = subidrunid(task)

        # apply mask 
        try:
            multmap = nimg.math_img('a*b',a=taskimg, b=maskimg) #element wise multiplication 
        except ValueError: # if shapes don't match
            print('Shapes of images do not match')
            print(f'mask image shape: {maskimg.shape}, task image shape {taskimg.shape}')
            print('Reshaping task to mask image dimensions...')
            taskimg = nimg.resample_to_img(source_img=taskimg,target_img=maskimg,interpolation='nearest')
            multmap = nimg.math_img('a*b',a=taskimg, b=maskimg) #element wise multiplication 
            newtask = f"/home/ws231/Downloads/repos/vibe_multivariate/scratch/{subid}_{runid.replace('.feat','')}_{task_name}.nii.gz"
            nib.save(taskimg, newtask)

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

            # us fsl cc to compare 

            fslcc = f'fslcc --noabs -m {gradient_mask_path} -t -1 {gradient} {newtask}'
            print(f'{gradient_mask_path}\n{gradient}\n{newtask}')
            # this runs the fsl command above
            p = subprocess.run(fslcc,shell=True, capture_output=True, text = True)
            print(p)
            fslcc_corr = p.stdout.split(' ')[6].strip('\n') #TOD0:hardcode 6?


            print ("Raw correlation:",corr)

            # apply fishers-r-to-z transformation to correlation value
            fcorr = np.arctanh(corr)

            print ("Fisher r-to-z transformed correlation:",fcorr)
            print('FSLCC:',fslcc_corr)

            # plot correlation of flattened arrays [mostly for testing but keeping for now]
            #plt.scatter(gradient_array.flatten(), task_array_masked.flatten(), marker='.')
            #plt.savefig(os.path.join(repo_path,f'scratch/plots/{task_name}_{gradnumber}_scatter.png'))
            #plt.close()

            # add necessary values to lists 

            taskids.append(task_name)
            gradientids.append(grad_name)
            correlations.append(np.round(corr,2))
            fcorrelations.append(np.round(fcorr,2))
            fslcc_correlations.append(fslcc_corr)


            if GroupLevelMaps == False:
                subids.append(subid)
                runids.append(runid)
            
    # create dataframe
    if GroupLevelMaps == False:
        df = pd.DataFrame({'sub_ID':subids,'run': runids, "gradient": gradientids, "input_map" : taskids ,"correlation": correlations, "fisher_correlation":fcorrelations,"fslcc_correlation":fslcc_correlations})

        df.to_csv(os.path.join(outputdir,f'gradscores_{corr_method}.csv'))
        return df


    else:
        df = pd.DataFrame({"input_map" : taskids, "gradient": gradientids, "fisher_correlation": fcorrelations})
        df_wide=pd.pivot(df, index=['input_map'], columns = 'gradient', values = "fisher_correlation") #Reshape from long to wide
        # Z-score each column and create new columns with the suffix '_z'
        for col in df_wide.columns:
            df_wide[col + '_z'] = zscore(df_wide[col])
        
        df_wide.to_csv(os.path.join(outputdir,f'gradscores_{corr_method}.csv'))
        return df_wide



def subidrunid(pth):
    """
    Function to extract subid and sesid from path
    """
    print('Warning: Assumes BIDS data structure.')
    splits = pth.split('/')[:-1] # extract every part of path except filename
    subid = [i for i in splits if 'sub-' in i]
    runid = [i for i in splits if 'run-' in i]
    assert len(subid) !=0
    assert len(runid) !=0
    return subid[0],runid[0]


