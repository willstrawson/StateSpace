'''
Create binarized mask from nifti image 

'''

import numpy as np
import nibabel as nib
import glob
import os
import pkg_resources

def binMask(method):

    gradient_subdir = pkg_resources.resource_filename('StateSpace','data/gradients')
    gradient_paths = sorted(glob.glob(f'{gradient_subdir}/*nii.gz'))
    
    if method == 'grad_only':

        mask_list = []
    
        # loop over grads (only necessary for sanity - all masks should be the same, regardless of which grad they came from)
        for brain_map in gradient_paths:
    
            map_array = nib.load(brain_map).get_fdata()
        
            mask = np.zeros_like(map_array)
        
            mask[map_array != 0] = 1
        
            mask_list.append(mask)
    
        if np.array_equal(mask_list[0],mask_list[1]):
            maskdir=pkg_resources.resource_filename('StateSpace', 'data/masks')
            # NOTE: See how we used the affine arg? this resolved weird aligmennt issue
            nib.save(nib.Nifti1Image(mask_list[0], affine=nib.load(brain_map).affine), 
            os.path.join(maskdir,'gradientmask_cortical.nii.gz'))
        else:
            print('Gradient 1 and 2 mask arrays do not match.')
            
    elif method == 'all_maps':
        
        task_subdir = pkg_resources.resource_filename('StateSpace','data/realTaskNiftis')
        task_paths = sorted(glob.glob(f'{task_subdir}/*nii.gz'))
        
        # put task and gradient maps together in a list to loop over
        all_paths = task_paths + gradient_paths
        
        mask_list = []
        
        # Loop over all maps
        for brain_map in all_paths:
            map_array = nib.load(brain_map).get_fdata()
            
            mask = np.zeros_like(map_array)
            
            mask[map_array != 0] = 1
            
            mask_list.append(mask)
        
        # Combine masks
        combined_mask = np.ones_like(mask_list[0])
        for mask in mask_list:
            combined_mask *= mask
            
        # Save final mask
        maskdir=pkg_resources.resource_filename('StateSpace', 'data/masks')
        nib.save(nib.Nifti1Image(combined_mask, affine=nib.load(brain_map).affine), 
                 os.path.join(maskdir,'combinedmask_cortical.nii.gz'))

        
        
        
        
        