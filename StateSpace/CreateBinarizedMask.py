'''
Create binarized mask from nifti image 

'''

import numpy as np
import nibabel as nib
import glob
import os
import pkg_resources

def binMask():

    gradient_subdir = pkg_resources.resource_filename('StateSpace','data/gradients')
    gradient_paths = sorted(glob.glob(f'{gradient_subdir}/*nii.gz'))


    #repo_path = os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
    #map_paths = sorted(glob.glob(os.path.join(repo_path, 'data/gradients/gradient*.nii.gz')))

    mask_list = []

    # loop over grads (only necessary for sanity - all masks should be the same, regardless of which grad they came from)
    for map in gradient_paths:

        map_array = nib.load(map).get_fdata()
    
        mask = np.zeros_like(map_array)
    
        mask[map_array != 0] = 1
    
        mask_list.append(mask)

    if np.array_equal(mask_list[0],mask_list[1]):
        maskdir=pkg_resources.resource_filename('StateSpace', 'data/masks')
        # NOTE: See how we used the affine arg? this resolved weird aligmennt issue
        nib.save(nib.Nifti1Image(mask_list[0], affine=nib.load(map).affine), 
        os.path.join(maskdir,'gradientmask_cortical.nii.gz'))
    else:
        print('Gradient 1 and 2 mask arrays do not match.')