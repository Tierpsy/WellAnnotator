#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 12:20:26 2020

@author: lferiani
"""

import h5py
import datetime
import pandas as pd
from pathlib import Path


WELLS_ANNOTATION_EXT = '_wells_annotations.hdf5'
FILES_DF_COLS = ['file_id', 'filename']
WELLS_ANNOTATIONS_DF_COLS = ['file_id',
                             'well_name',
                             'x_min',
                             'x_max',
                             'y_min',
                             'y_max',
                             'well_label']

WELL_LABELS = {1: 'good',
               2: 'misaligned',
               3: 'precipitation',
               4: 'contamination',
               5: 'wet',
               6: 'bad agar',
               7: 'other bad',
               }

BTN_COLOURS = {1: 'green',
               2: 'darkRed',
               3: 'yellow',
               4: 'brown',
               5: 'magenta',
               6: 'darkCyan',
               7: 'orange',
               }

BUTTON_STYLESHEET_STR = (
    "QPushButton:checked "
    + "{border: 2px solid; border-radius: 6px; background-color: %s }"
    )


def _is_child_of_maskedvideos(input_path: Path):
    return 'MaskedVideos' in input_path.parts


def check_good_input(input_path: Path):
    if isinstance(input_path, str):
        input_path = Path(input_path)
    if input_path.is_dir():
        assert _is_child_of_maskedvideos(input_path), \
            'input_path should be MaskedVideos or its subfolder'
    else:
        assert input_path.name.endswith('hdf5'), 'Please enter an hdf5 file.'
        with pd.HDFStore(input_path, 'r') as fid:
            assert 'filenames_df' in fid, 'Input file missing /filenames_df'
            assert 'wells_annotations_df' in fid, (
                'Input file missing /wells_annotations_df')

    return True


def find_wellsanns_file_in_dir(working_dir: Path):
    """
    Scan the folder working_dir looking for a wells annotation file with
    existing progress. Return the path to the file if found, None if not.

    Parameters
    ----------
    working_dir : pathlib's Path
        The path to scan for a file that ends in _wells_annotations.hdf5

    Raises
    ------
    ValueError
        If more than one _wells_annotations.hdf5 file is found in working_dir.

    Returns
    -------
    annotation_file : Path
        path to the annotations file.

    """

    # look for the annotation file
    annotation_files = list(working_dir.rglob('*'+WELLS_ANNOTATION_EXT))
    # handle output
    if len(annotation_files) == 0:
        annotation_file = None
    elif len(annotation_files) == 1:
        annotation_file = annotation_files[0]
    else:
        raise ValueError(("More than one wells annotations file found. "
                          + "Don't know what to do. Aborting."))

    return annotation_file


def get_project_root(working_dir: Path):
    """
    Scan the parts of working_dir for a folder named MaskedVideos.
    Then return its parent

    Parameters
    ----------
    working_dir : Path
        Path to working folder.

    Returns
    -------
    proj_root_dir : Path, or None
        Path to the project root (assuming it's MaskedVideos' parent).

    """
    proj_root_dir = None
    dirlist = [working_dir] + list(working_dir.parents)
    for dirname in dirlist:
        # do sth only if this folder is named MaskedVideos
        if not dirname.name == 'MaskedVideos':
            continue
        # but not if you have already done something
        if proj_root_dir is not None:
            continue
        # get path of parent. Assume standard proj folder structure
        proj_root_dir = dirname.parent

    return proj_root_dir


def name_new_wellsanns_file(working_dir: Path):
    """
    Assemble a new name by stitching the project name, a datetime, and the
    "_wells_annotations.hdf5" ending.

    Parameters
    ----------
    working_dir : Path
        Path to working folder.

    Returns
    -------
    new_wellsanns_path : Path
        Suggested path for a new wells annotations file .

    """
    # get project name
    proj_root_path = get_project_root(working_dir)
    # get datetime
    datetime_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    # assemble the new files name
    if proj_root_path is not None:
        new_wellsanns_fname = proj_root_path.name + '_'
    else:
        new_wellsanns_fname = ''
    new_wellsanns_fname += (datetime_str + WELLS_ANNOTATION_EXT)
    # and its path
    new_wellsanns_path = working_dir / new_wellsanns_fname
    # then move it to auxiliary files
    new_wellsanns_path = masked2aux(new_wellsanns_path)

    return new_wellsanns_path


def get_list_masked_videos(working_dir: Path, is_prestim_only: bool = True):
    """
    Get list of *.hdf5 files in working_dir. filter out any wells_annotations

    Parameters
    ----------
    working_dir : Path
        Path to working folder. Has already been checked to belon

    Returns
    -------
    fnames : list[Path]
        List of Path objects to masked videos.

    """

    # get all hdf5
    fnames = working_dir.rglob('*.hdf5')
    # jsut make sure that for some weird reason there is not wellsanns file...
    fnames = [f for f in fnames if not f.name.endswith(WELLS_ANNOTATION_EXT)]
    if is_prestim_only:
        fnames = [f for f in fnames if 'prestim' in str(f)]

    return fnames


def initialise_annotations_file(working_dir: Path,
                                is_prestim_only: bool = True):
    # get name of the file we need to create
    wellsanns_fname = name_new_wellsanns_file(working_dir)
    # get list of files in working_dir
    masked_fnames = get_list_masked_videos(working_dir,
                                           is_prestim_only=is_prestim_only)
    # make it relative
    masked_fnames = [str(f.relative_to(working_dir)) for f in masked_fnames]
    # create files dataframe
    fnames_df = pd.DataFrame({'file_id': range(len(masked_fnames)),
                              'filename': masked_fnames})
    # write df in file, delete anything inside it
    wellsanns_fname.parent.mkdir(exist_ok=True, parents=True)
    fnames_df.to_hdf(wellsanns_fname,
                     key='/filenames_df',
                     index=False,
                     mode='w')

    with h5py.File(wellsanns_fname, 'r+') as fid:
        fid["/filenames_df"].attrs["working_dir"] = str(working_dir)

    # create df for wells annotations
    wellsanns_df = pd.DataFrame(data=None, columns=WELLS_ANNOTATIONS_DF_COLS)
    # add it to the file
    wellsanns_df.to_hdf(wellsanns_fname,
                        key='/wells_annotations_df',
                        index=False,
                        mode='r+')

    return wellsanns_fname


def masked2aux(input_path):
    return Path(str(input_path).replace('MaskedVideos', 'AuxiliaryFiles'))


def get_or_create_annotations_file(input_path: Path,
                                   is_prestim_only: bool = True):
    # fix type
    if isinstance(input_path, str):
        input_path = Path(input_path)
    # input check. Needs to be either the right file, or
    # a folder downstream of MaskedVideos
    _ = check_good_input(input_path)
    if not input_path.is_dir():
        wellsanns_fname = input_path
    else:
        # if a file exists get its name
        target_dir = masked2aux(input_path)
        wellsanns_fname = find_wellsanns_file_in_dir(target_dir)
        # if not, create it
        if wellsanns_fname is None:
            wellsanns_fname = initialise_annotations_file(
                input_path, is_prestim_only=is_prestim_only)

    return wellsanns_fname


def _rebase_annotations(wells_annotations_filename: Path,
                        new_working_dir: Path):

    # fix type. let's use paths even if we could do with strings, can help
    # in the future if I expand
    if isinstance(wells_annotations_filename, str):
        wells_annotations_filename = Path(wells_annotations_filename)
    if isinstance(new_working_dir, str):
        new_working_dir = Path(new_working_dir)

    # do some checks
    assert wells_annotations_filename.exists(), 'Annotations file not found'
    assert new_working_dir.exists(), 'new_working_dir not found'
    # should I check that the target files are found in the new path? dunno yet

    # actual body of the function
    with h5py.File(wells_annotations_filename, 'r+') as fid:
        # store old one as well, and print it out to the user
        old_working_dir = fid["/filenames_df"].attrs["working_dir"]
        print(f"old working directory: {old_working_dir}")
        fid["/filenames_df"].attrs["previous_working_dir"] = old_working_dir
        # write the new one
        fid["/filenames_df"].attrs["working_dir"] = str(new_working_dir)

    return


def rebase_annotations():
    """
    rebase_annotations In the well annotations hdf5 file, the video name is
        only saved relative to the working directory. The working directory
        is saved as an attribute to the /filenames_df table.
        This can cause issues if a user decides to move data to a different
        drive or a different directory.
        This utility allows the user to change the working directory.

    Parameters
    ----------
    wells_annotations_filename : Path
        Path (either absolute or relative to the folder from where you're
        calling the tool) to the annotations hdf5 file
    new_working_dir : Path
        Path to the new working directory

    """
    import fire
    fire.Fire(_rebase_annotations)


def _read_working_dir(wells_annotations_filename):
    with h5py.File(wells_annotations_filename, 'r+') as fid:
        print(fid["/filenames_df"].attrs["working_dir"])
    return


def read_working_dir():
    """
    read_working_dir Quick tool to read the working directory of a wells
        annotation hdf5 file.

    Parameters
    ----------
    wells_annotations_filename : Path
        Path (either absolute or relative to the folder from where you're
        calling the tool) to the annotations hdf5 file
    """
    import fire
    fire.Fire(_read_working_dir)


if __name__ == "__main__":

    input_str = '/Users/lferiani/work_repos/WellAnnotator/data/MaskedVideos'
    # input_str = '/Users/lferiani/work_repos/WellAnnotator/data/MaskedVideos/data_20200715_152507_wells_annotations.hdf5'
    annotations_file = get_or_create_annotations_file(input_str)
    # out = ask_if_prestim_only()
    # print(out)





