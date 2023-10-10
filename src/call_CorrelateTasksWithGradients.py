# -*- coding: utf-8 -*-

'''
Correlate task maps with Gradients to produce state-space coordinates.

Using 'all maps' mask.

'''
import os
from StateSpace import CorrelateTasksWithGradients

# get path to output dir 
outputdir = os.path.join(os.path.split(os.path.split(os.path.realpath(__file__))[0])[0], 'scratch')

if os.path.exists(outputdir) == False: #If scratch doesn't exist 
    os.mkdir(outputdir)

## COMBINED MASKS

# Combined mask, cortical only
CorrelateTasksWithGradients.corrTasks('combinedmask_cortical',
                                      'cortical_only',
                                      outputdir, verbose = 1)

# Combined mask, cortical and subcortical
CorrelateTasksWithGradients.corrTasks('combinedmask_cortical_subcortical',
                                      'all',
                                      outputdir, verbose = 1)

# Combined mask, cortical only, z-scored
CorrelateTasksWithGradients.corrTasks('combinedmask_cortical',
                                      'cortical_only',
                                      outputdir, verbose = 1,
                                      z_score=True)

# Combined mask, cortical and subcortical, z-scored
CorrelateTasksWithGradients.corrTasks('combinedmask_cortical_subcortical',
                                      'all',
                                      outputdir, verbose = 1,
                                      z_score=True)


## GRADIENT-ONLY MASKS

# Gradient mask, cortical only
CorrelateTasksWithGradients.corrTasks('gradientmask_cortical',
                                      'cortical_only',
                                      outputdir, verbose = 1)

# Gradient mask, cortical and subcortical
CorrelateTasksWithGradients.corrTasks('gradientmask_cortical_subcortical',
                                      'all',
                                      outputdir, verbose = 1)

# Gradient mask, cortical only, z-scored
CorrelateTasksWithGradients.corrTasks('gradientmask_cortical',
                                      'cortical_only',
                                      outputdir, verbose = 1,
                                      z_score=True)

# Gradient mask, cortical and subcortical, z-scored
CorrelateTasksWithGradients.corrTasks('gradientmask_cortical_subcortical',
                                      'all',
                                      outputdir, verbose = 1,
                                      z_score=True)