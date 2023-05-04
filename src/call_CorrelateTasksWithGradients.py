# -*- coding: utf-8 -*-

'''
Correlate task maps with Gradients to produce state-space coordinates.

'''
import glob
import os
from StateSpace import CorrelateTasksWithGradients

# get path to output dir 
outputdir = os.path.join(os.path.split(os.path.split(os.path.realpath(__file__))[0])[0], 'scratch')

if os.path.exists(outputdir) == False: #If scratch doesn't exist 
    os.mkdir(outputdir)

CorrelateTasksWithGradients.corrTasks(outputdir)



        



