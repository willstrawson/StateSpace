# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import os
import shutil
import nibabel as nib
import numpy as np
from nilearn.datasets import fetch_atlas_schaefer_2018, fetch_atlas_yeo_2011
from nilearn.image import load_img, new_img_like, resample_to_img
from tqdm import tqdm
import pkg_resources


def makemaps(
    yeo: bool, splitmaps: bool, shafer_rois: int = 400, yeover: str = "thick_7"
):
    """
    This function makes a parcellation map from either the Yeo or Shafer atlas.

    Parameters
    ----------
    yeo : bool
        Whether to use the Yeo atlas.
    splitmaps : bool
        Whether to split the Yeo atlas into separate maps.
    shafer_rois : int
        Number of ROIs to use in the Shafer atlas.
    yeover : str
        Which version of the Yeo atlas to use.
        Options: "thick_7", "thick_17", "thin_7", "thin_17"

    Returns
    -------
    parcellation : nibabel.nifti1.Nifti1Image
        The parcellation map.
    parcelnames : list
        The names of the parcels.
    """
    if yeo:
        yeonum = yeover.split("_")[-1]
        atlasdir = "yeo_networks"
        parcellation = load_img(fetch_atlas_yeo_2011(atlasdir)[yeover])
        if splitmaps:
            mdata = np.squeeze(parcellation.get_fdata())
            for i in range(int(yeonum)):
                i = i + 1
                mdata_ = np.where(np.logical_and(mdata != 0, mdata != i), 10, mdata)
                mdata_ = np.where(mdata_ == i, 100, mdata_)
                mapn = new_img_like(parcellation, mdata_)
                nib.save(mapn, f"yeo_{yeonum}_{i}.nii.gz")
            return
        if yeonum == "17":
            parcelnames = [
                b"VisCent",
                b"VisPeri",
                b"Somatomotor A",
                b"Somatomotor B",
                b"Dorsal Attention A",
                b"Dorsal Attention B",
                b"Salience/Ventral Attention A",
                b"Salience/Ventral Attention B",
                b"Limbic B",
                b"Limbic A",
                b"Control A",
                b"Control B",
                b"Control C",
                b"Temporal Parietal",
                b"Default A",
                b"Default B",
                b"Default C",
            ]
        elif yeonum == "7":
            parcelnames = [
                b"Visual",
                b"Somatomotor",
                b"Dorsal Attention",
                b"Ventral Attention",
                b"Limbic",
                b"Frontoparietal",
                b"Default",
            ]
    else:
        atlasdir = "shaefer_atlas"
        parcellation = fetch_atlas_schaefer_2018(n_rois=shafer_rois, data_dir=atlasdir)
        parcelnames = parcellation["labels"].tolist()
        parcellation = load_img(parcellation["maps"])
    return parcellation, parcelnames


def lesion(
    lesionnumber: int,
    parcel: str,
    parcellation: nib.Nifti1Image,
    mapdir: str,
    outpath: str,
):
    """
    This function takes a lesion number, a parcel name, a parcellation, a map directory, and an output path.
    It then creates a new directory in the output path with the name of the parcel.
    It then resamples the parcellation to the maps in the map directory.
    It then creates a new map for each map in the map directory where the lesion number is set to 0.
    It then saves the new maps in the new directory.
    """
    lesionnumber += 1
    maps = [[x, nib.load(os.path.join(mapdir, x))] for x in os.listdir(mapdir) if '.nii' in x] # add extension check for README
    print(maps)
    fixed_parcelmap = (
        resample_to_img(parcellation, maps[0][1], interpolation="nearest")
        .get_fdata()
        .squeeze()
    )
    for map in maps:
        mapname = map[0]
        map = map[1]
        mapdata = map.get_fdata()
        # exclude parcel 
        mapdata_exclude = np.where(fixed_parcelmap == lesionnumber, 0, mapdata)
        # include parcel 
        mapdata_include = np.where(fixed_parcelmap != lesionnumber, 0, mapdata)

        mapnifti = new_img_like(map, mapdata_exclude, affine=map.affine)
        mapnifti.to_filename(os.path.join(outpath, parcel.decode(), f'ex_{mapname}'))
        print(f'Saving {os.path.join(outpath, parcel.decode(), mapname)}')

        mapnifti = new_img_like(map, mapdata_include, affine=map.affine)
        mapnifti.to_filename(os.path.join(outpath, parcel.decode(), f'in_{mapname}'))
        print(f'Saving {os.path.join(outpath, parcel.decode(), mapname)}')

