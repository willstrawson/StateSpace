# -*- coding: utf-8 -*-
#!/usr/bin/env python3

'''
Create binarized mask from nifti image 

'''


import glob
import os
from StateSpace import Lesion
import pkg_resources
import os
import shutil
from tqdm import tqdm

if __name__ == "__main__":

    yeo = True
    splitmaps = False

    # use pkg_resources to access the absolute path for each data subdirectory 
    gradient_subdir = pkg_resources.resource_filename('StateSpace','data/gradients') # path to input gradient
    task_subdir = pkg_resources.resource_filename('StateSpace','data/realTaskNiftis') # path to input task maps 
    datadir = pkg_resources.resource_filename('StateSpace','data') # for output 

    print(task_subdir)

    path = os.path.join(f'{datadir}/lesionedOutputs') # store data in the same place as other 
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)

    parcellation, parcelnames = Lesion.makemaps(yeo, splitmaps, yeover="thick_7")

    for en, parcel in tqdm(enumerate(parcelnames)):
        patht = os.path.join(path, parcel.decode())
        if os.path.exists(patht):
            shutil.rmtree(patht)
        os.mkdir(patht)

        Lesion.lesion(en, parcel, parcellation, task_subdir, path)
        Lesion.lesion(en, parcel, parcellation, gradient_subdir, path)