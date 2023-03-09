# -*- coding: utf-8 -*-

'''
Create binarized mask from nifti image 

'''
import glob
from StateSpace import CorrelateTasksWithGradients

#CorrelateTasksWithGradients.corrTasks("/Users/willstrawson/Documents/PhD/repos/StateSpace/scratch")

CorrelateTasksWithGradients.corrTasks("/Users/willstrawson/Documents/PhD/repos/StateSpace/scratch",
inputfiles=glob.glob('/Users/willstrawson/Documents/PhD/Rotation_2/fMRI/lev_2/allps_avhsruns_0.2.gfeat/cope10.feat/stats/zstat*.nii.gz'))




        



