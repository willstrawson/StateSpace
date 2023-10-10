# -*- coding: utf-8 -*-
#!/usr/bin/env python3

'''
Correlate task maps with pain signature to produce state-space coordinates.
'''

import os
from StateSpace import CorrelateTasksWithGradients

# get path to output dir 
outputdir = os.path.join(os.path.split(os.path.split(os.path.realpath(__file__))[0])[0], 'scratch')

if os.path.exists(outputdir) == False: #If scratch doesn't exist 
    os.mkdir(outputdir)

## COMBINED MASKS

"""
CorrInd Args: 
mask_name, 
map_coverage, 
inputfiles, 
outputdir,
taskstring, 
substring, 
runstring = None,
corr_method='spearman', 
verbose=-1):

"""

# Full mask (created from binairizing vps .nii), cortical only 
CorrelateTasksWithGradients.corrInd('combinedmask_cortical',
                                      'cortical_only',
                                      outputdir, verbose = 1)

# Full mask (created from binairizing vps .nii), cortical and subccortical
CorrelateTasksWithGradients.corrInd('combinedmask_cortical_subcortical',
                                      'all',
                                      outputdir, verbose = 1)

# Full mask (created from binairizing vps .nii), cortical only, z scored 
CorrelateTasksWithGradients.corrInd('combinedmask_cortical',
                                      'cortical_only',
                                      outputdir, verbose = 1,
                                      z_score=True)

# Full mask (created from binairizing vps .nii), cortical and subccortical, z scored 
CorrelateTasksWithGradients.corrInd('combinedmask_cortical_subcortical',
                                      'all',
                                      outputdir, verbose = 1,
                                      z_score=True)

