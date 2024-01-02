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
inputfiles = glob.glob('C:\\Users\\bront\\Documents\\500days\\derivatives\\sub_*\\func\\sub-*_task-500daysofsummer_bold_blur_censor_cut.nii.gz')

# set the name of the mask you are using ('gradientmask_cortical_subcortical' or 'gradientmask_cortical') and the gradient coverage you want ('all' or 'cortical_only')
mask_name = 'gradientmask_cortical_subcortical'
map_coverage = 'all'

# call calGroupTimeCourse on list of input files to calculate the group-averaged time course (z-score = True if you want to z-score ind maps before averaging)
group_array_masked = CorrelateTasksWithGradients.calGroupTimeCourse(mask_name, map_coverage, inputfiles, z_score = True, verbose=1)

# call corrGroupTimeCourse on group-averaged array (masked) to correlate group array with gradients
# set string to output name e.g., "500days-zscore", set verbose to 1 if you want print statements
CorrelateTasksWithGradients.corrGroupTimeCourse(mask_name,
                                                map_coverage, 
                                                "500days-zscore",
                                                group_array_masked,
                                                outputdir,
                                                corr_method='spearman',
                                                verbose=1)

print ("end")
