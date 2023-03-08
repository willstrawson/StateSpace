# -*- coding: utf-8 -*-

'''
Create binarized mask from nifti image 

'''

from StateSpace import CorrelateTasksWithGradients

CorrelateTasksWithGradients.corrTasks("C:\\Users\\bront\\Documents\\repos\\StateSpace\\scratch\\results",
                                      "spearman",
                                      saveMaskedimgs = True)


        



