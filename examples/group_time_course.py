'''
Correlates group time series of 500 days of summer with Gradients to produce group-averaged state-space coordinates.

To run, make a copy in your analysis directory.

'''
import os
import glob 
from StateSpace import CorrelateTasksWithGradients

# get path to output dir 
outputdir = os.path.join(os.path.split(os.path.split(os.path.realpath(__file__))[0])[0], 'results')

if os.path.exists(outputdir) == False: #If results doesn't exist, make results directory
    os.mkdir(outputdir)

# use glob to select all files you want to analyse and store them in a list
inputfiles = glob.glob('C:\\Users\\bront\\Downloads\\sub-10_task-500daysofsummer_bold_blur_censor_cut.nii.gz')

# set the name of the mask you are using and the gradient coverage you want (all or cortical_only)
mask_name = 'gradientmask_cortical_subcortical'
map_coverage = 'all'

# call calGroupTimeCourse on list of input files to calculate the group-averaged time course
group_array_masked = CorrelateTasksWithGradients.calGroupTimeCourse(mask_name, map_coverage, inputfiles, z_score = True, verbose=1)

# call corrGroupTimeCourse on group-averaged array (masked) to correlate group array with gradients
CorrelateTasksWithGradients.corrGroupTimeCourse(mask_name,
                                                map_coverage, 
                                                "500days",
                                                group_array_masked,
                                                outputdir,
                                                corr_method='spearman',
                                                verbose=1)

print ("end")