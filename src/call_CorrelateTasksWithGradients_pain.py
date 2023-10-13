# -*- coding: utf-8 -*-
#!/usr/bin/env python3

'''
Correlate task maps with pain signature to produce state-space coordinates.
'''
# TODO: Reacreate previous results 
# 1. Use NPS with NPS mask
# 2. Use NPS with GM mask
# 3. Use new VPS with VPS mask
# 4. Use new VPS with GM mask 

import os
import glob
from StateSpace import CorrelateTasksWithGradients

# get path to output dir 
outputdir = os.path.join(os.path.split(os.path.split(os.path.realpath(__file__))[0])[0], 'scratch')

#inputfiles = glob.glob('/Users/willstrawson/Documents/PhD/repos/StateSpace/StateSpace/data/realTaskNiftis_Ind/sub-*/run-*/*')
inputfiles = glob.glob('/research/cisc1/projects/ward_painsig/VolumeData2_3D/*.nii')

if os.path.exists(outputdir) == False: #If scratch doesn't exist 
    os.mkdir(outputdir)

## COMBINED MASKS

"""
CorrInd Args: 
data [pain/gradients],
sim_metric [corr, dotproduct],
mask_name, 
map_coverage,  # not used 
inputfiles, 
outputdir,
taskstring, 
substring, 
runstring = None,
corr_method='spearman', 
verbose=-1):

"""

# Full mask (created from binairizing vps .nii), cortical and subccortical
CorrelateTasksWithGradients.corrInd(
    'pain', # use any .nii found in from data/pain dir (e.g. VPS)
    'dotproduct', # use dot product as similarity score
    'vps_2020', # use the vps_2020.nii 
    inputfiles, # list of input files 
    outputdir, # put in repo scratch/ 
    '.nii', # get contrast name by splitting  head of file name e.g. /research/cisc1/projects/ward_painsig/VolumeData2_3D/CISC123_results_picture_00032.nii by _ and detect substrinng comntaining .nii
    'CISC') # get subid by splitting head of filename and detect substring containning 'CISC'

'''
# Full mask (created from binairizing vps .nii), cortical and subccortical
CorrelateTasksWithGradients.corrInd(
    'pain',
    'dot',
    'combinedmask_cortical_subcortical',
    inputfiles,
    outputdir,
    '.nii',
    'CISC')



# Full mask (created from binairizing vps .nii), cortical and subccortical
CorrelateTasksWithGradients.corrInd(
    'pain',
    'vps_2020',
    'all',
    outputdir, 
    verbose = 1)

# Full mask (created from binairizing vps .nii), cortical and subccortical, z scored 
CorrelateTasksWithGradients.corrInd(
    'pain'
    'vps_2020',                                  
    'all',
    outputdir, 
    verbose = 1,
    z_score=True)
'''

