# -*- coding: utf-8 -*-

'''
Create binarized masks from nifti images

1. from gradients only
2. from all maps

'''

from StateSpace import CreateBinarizedMask

CreateBinarizedMask.binMask(method = 'grad_only')

CreateBinarizedMask.binMask(method = 'all_maps')


        



