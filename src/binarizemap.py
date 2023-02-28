# -*- coding: utf-8 -*-

'''
Create binarized mask from nifti image 
'''

import numpy as np
import nibabel as nib
import glob

map_paths = glob.glob('/Users/willstrawson/Documents/PhD/CanadianGradients/data/gradients/gradient*.nii.gz')

mask_list = []
# loop over grads (only necessary for sanity - all masks should be the same, regardless of which grad they came from)
for map in map_paths:

    map_array = nib.load(map).get_fdata()

    mask = np.zeros_like(map_array)

    mask[map_array != 0] = 1

    mask_list.append(mask)

if np.array_equal(mask_list[0],mask_list[2]):
    # NOTE: See how we used the affine arg? this resolved weird aligmennt issue
    nib.save(nib.Nifti1Image(mask_list[0], affine=nib.load(map).affine), 
    '/Users/willstrawson/Documents/PhD/CanadianGradients/data/masks/gradientmask_cortical.nii.gz')
else:
    print(' YOU FUCKED IT ')

