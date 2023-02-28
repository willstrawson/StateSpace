# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 08:17:21 2023

@author: bront

Script to call CorrelateTasksWithGradients module.

"""

from StateSpace import CorrelateTasksWithGradients

CorrelateTasksWithGradients.corrTasks('C://Users//bront//Documents//CanadaPostdoc//MegaProject//MegaProject//scratch//results//gradScores',
                                      corr_method= 'spearman')


