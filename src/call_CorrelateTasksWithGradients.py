# -*- coding: utf-8 -*-

'''
Create binarized mask from nifti image 

'''

from StateSpace import CorrelateTasksWithGradients

CorrelateTasksWithGradients.corrTasks("/Users/willstrawson/Documents/PhD/repos/StateSpace/scratch",
                                      "spearman",
                                      saveMaskedimgs = True)


        



