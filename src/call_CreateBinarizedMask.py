# -*- coding: utf-8 -*-

'''
Create binarized masks from nifti images

1. from gradients only (cortical only AND cortical-subcortical)
2. from all maps (cortical only AND cortical-subcortical)

'''

from StateSpace import CreateBinarizedMask

CreateBinarizedMask.binMask(method = 'grad_only', map_coverage = 'all')
CreateBinarizedMask.binMask(method = 'grad_only', map_coverage = 'cortical_only')

CreateBinarizedMask.binMask(method = 'all_maps', map_coverage = 'all')
CreateBinarizedMask.binMask(method = 'all_maps', map_coverage = 'cortical_only')



        



