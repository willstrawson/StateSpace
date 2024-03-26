import nibabel as nib
from nilearn import image as nimg
import glob
from scipy.stats import spearmanr, pearsonr
import os 
import pandas as pd
import numpy as np
import pkg_resources
from scipy.stats import zscore

def checkLength(input_files):
    # Check if there are any input files
    if not input_files:
        print("No input files found.")
    else:
        # Load the first file to get its shape
        first_file = nib.load(input_files[0])
        print (first_file.shape)
        first_shape = first_file.shape

    # Iterate through the rest of the files and check if their fourth dimension sizes match
    for file_path in input_files[1:]:
        current_file = nib.load(file_path)
        print (current_file.shape)
        current_shape = current_file.shape

        # Check if the fourth dimension size matches
        if first_shape[3] != current_shape[3]:
            print(f"Error: The TR length of {file_path} does not match the TR length of the first file.")
            break
    else:
        print("All input files have the same TR length.")