#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 12:20:26 2020

@author: lferiani
"""

import cv2
import h5py
import torch
import datetime
import numpy as np
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
               8: 'bad lawns',
               9: 'bad worms',
               }

BTN_COLOURS = {1: 'green',
               2: 'darkRed',
               3: 'yellow',
               4: 'brown',
               5: 'magenta',
               6: 'darkCyan',
               7: 'orange',
               8: 'purple',
               9: 'red',
               }

BUTTON_STYLESHEET_STR = (
    "QPushButton:checked "
    + "{border: 2px solid; border-radius: 6px; background-color: %s }"
    )


def _is_child_of_tierpsy_out_dir(input_path: Path):
    is_it = 'MaskedVideos' in input_path.parts
    is_it = is_it | ('Results' in input_path.parts)
    return is_it


def check_good_input(input_path: Path):
    if isinstance(input_path, str):
        input_path = Path(input_path)
    if input_path.is_dir():
        assert _is_child_of_tierpsy_out_dir(input_path), \
            'input_path should contain MaskedVideos or Results'
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
    Scan the parts of working_dir for a folder named MaskedVideos or Results.
    Then return its parent

    Parameters
    ----------
    working_dir : Path
        Path to working folder.

    Returns
    -------
    proj_root_dir : Path, or None
        Path to the project root
        (assuming it's MaskedVideos' or Results' parent).

    """
    proj_root_dir = None
    dirlist = [working_dir] + list(working_dir.parents)
    for dirname in dirlist:
        # do sth only if this folder is one of the standard tierpsy ones
        if dirname.name not in ['MaskedVideos', 'Results']:
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
    new_wellsanns_path = tierpsyoutdir2aux(new_wellsanns_path)

    return new_wellsanns_path


def get_list_masked_or_feats(working_dir: Path, is_prestim_only: bool = True):
    """
    Get list of *.hdf5 files in working_dir. filter out any wells_annotations

    Parameters
    ----------
    working_dir : Path
        Path to working folder. Has already been checked to belon

    Returns
    -------
    fnames : list[Path]
        List of Path objects to masked or features videos.

    """

    # get all the hdf5 that could contain /fov_wells info
    fnames = working_dir.rglob('*.hdf5')
    if 'Results' in working_dir.parts:
        fnames = [f for f in fnames if f.name.endswith('_featuresN.hdf5')]
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
    tierpsy_fnames = get_list_masked_or_feats(
        working_dir, is_prestim_only=is_prestim_only)
    ass_msg = 'Could not find any video, aborting. '
    if is_prestim_only:
        ass_msg += 'You could retry without `prestimulus only`.'
    assert len(tierpsy_fnames) > 0, ass_msg
    # make it relative
    tierpsy_fnames = [str(f.relative_to(working_dir)) for f in tierpsy_fnames]
    # create files dataframe
    fnames_df = pd.DataFrame({'file_id': range(len(tierpsy_fnames)),
                              'filename': tierpsy_fnames})
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


def tierpsyoutdir2aux(input_path):
    aux_path = (
        str(input_path)
        .replace('MaskedVideos', 'AuxiliaryFiles')
        .replace('Results', 'AuxiliaryFiles')
        )
    return Path(aux_path)


def mask2feats(input_path):
    _is_return_str = isinstance(input_path, str)
    out_path = (
        str(input_path)
        .replace('MaskedVideos', 'Results')
        .replace('.hdf5', '_featuresN.hdf5')
        )
    if not _is_return_str:
        out_path = Path(out_path)
    return out_path


def tierpsyfile2raw(input_path):
    _is_return_str = isinstance(input_path, str)
    raw_fname = Path(
        input_path
        .replace('MaskedVideos', 'RawVideos')
        .replace('Results', 'RawVideos')
        .replace('_featuresN.hdf5', '*')
        .replace('.hdf5', '.*')
        )
    raw_candidates = list(raw_fname.parent.rglob(raw_fname.name))
    assert len(raw_candidates) > 0, f'No videos found for {input_path}'
    assert len(raw_candidates) == 1, f'Multiple videos for {input_path}'
    raw_fname = raw_candidates[0]
    if _is_return_str:
        raw_fname = str(raw_fname)
    return raw_fname


def get_or_create_annotations_file(input_path: Path,
                                   is_prestim_only: bool = True):
    # fix type
    if isinstance(input_path, str):
        input_path = Path(input_path)
    # input check. Needs to be either the right file, or
    # a folder downstream of MaskedVideos or Results
    _ = check_good_input(input_path)
    if not input_path.is_dir():
        wellsanns_fname = input_path
    else:
        # if a file exists get its name
        target_dir = tierpsyoutdir2aux(input_path)
        wellsanns_fname = find_wellsanns_file_in_dir(target_dir)
        # if not, create it
        if wellsanns_fname is None:
            wellsanns_fname = initialise_annotations_file(
                input_path, is_prestim_only=is_prestim_only)

    return wellsanns_fname


def load_CNN_models():
    """
    load_CNN_models Load the CNN models used for inference from disk

    Returns
    -------
    list
        list of models
    """
    from well_annotator import base_path
    from well_annotator.trained_models.cnn_definition import (
        CNNFromTierpsy, CNNFromTierpsyShallower, CNNFromTierpsyEvenShallower)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    models_path = base_path / 'trained_models'
    # list of model filenames and the right class to use
    models_to_load = [
        ('v_01_58_best.pth', CNNFromTierpsy),
        ('v_01_54_best.pth', CNNFromTierpsy),
        ('v_02_54_20220224_231530.pth',  CNNFromTierpsyShallower),
        ('v_04_53_best.pth', CNNFromTierpsyEvenShallower),
        ('v_04_58_20220324_105528.pth', CNNFromTierpsyEvenShallower),
    ]

    # load models and their weights, send to right device, put in eval mode
    # and add to list to return
    models = []
    for model_name, ModelClass in models_to_load:
        model_fname = models_path / model_name
        checkpoint = torch.load(model_fname, map_location=device)
        model = ModelClass()
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(device)
        model.eval()
        models.append(model)

    return models


def preprocess_images_for_CNN(images, device=None):
    """
    preprocess_images_for_CNN
    crop, resize, normalise, tensorify, send to device

    Parameters
    ----------
    images : numpy array
        n_frames x height x width, uint8

    Returns
    -------
    torch tensor
        n_frames x 1 x 160 x 160, float
    """

    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    crop_sz = 640  # crop size before resizing
    img_sz = 160  # size of the image after resizing, dictated by the CNN
    ds_mean = 93.37299001461375 / 255
    ds_std = 54.632948105068145 / 255

    # crop
    n_imgs, height, width = images.shape
    top_pad = (height - crop_sz) // 2
    left_pad = (width - crop_sz) // 2
    images_out = images[
        :, top_pad:top_pad + crop_sz, left_pad:left_pad + crop_sz]
    # resize, using transpose so n_images uses the colour channel for cv2
    # since cv2 knows how to resize an image with a colour channel
    images_out = images_out.transpose((1, 2, 0))
    images_out = cv2.resize(
        images_out, (img_sz, img_sz), interpolation=cv2.INTER_AREA)
    # transpose for pytorch i.e. n_images, n_colours, img_sz, img_sz
    images_out = images_out.transpose((2, 0, 1))[:, None, :, :]
    # cast and normalize
    images_out = torch.from_numpy(images_out).float().div(255)
    images_out = (images_out - ds_mean) / ds_std

    return images_out.to(device)


def apply_one_model(model, images, prediction_threshold=0.3):
    """
    Run inference on images using one model
    since each batch are multiple frames from the same well, apply majority
    voting to the predictions of each frame by the same model.
    Return one prediction only
    """

    with torch.no_grad():
        # inference, and get predictions
        batch_logits = model(images)
        batch_probas = torch.sigmoid(batch_logits).cpu().numpy()
        batch_predictions = batch_probas > prediction_threshold
        # apply majority voting to all predictions of the same well/batch
        uniq_pred, pred_count = np.unique(
            batch_predictions, return_counts=True)
        prediction = uniq_pred[np.argmax(pred_count)]

    return prediction


def majority_vote(models, images, prediction_threshold=0.3):
    """
    Run inference on images using multiple models
    return the majority vote (i.e. mode) across the predictions of each model
    """

    # inference on all models
    models_predictions = [
        apply_one_model(model, images, prediction_threshold)
        for model in models]

    # get the most common prediction
    majority_prediction = mode_fun(models_predictions)

    return majority_prediction


def mode_fun(input_array):
    """
    numpy implementation of mode function
    """
    uu, cc = np.unique(input_array, return_counts=True)
    mode_value = uu[np.argmax(cc)]
    return mode_value


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
    old_wrk_dir = _read_working_dir(wells_annotations_filename)
    with h5py.File(wells_annotations_filename, 'r+') as fid:
        # store old one as well, and print it out to the user
        if len(old_wrk_dir) > 0:
            print(f"old working directory: {old_wrk_dir}")
            fid["/filenames_df"].attrs["previous_working_dir"] = old_wrk_dir
        # write the new one
        fid["/filenames_df"].attrs["working_dir"] = str(new_working_dir)

    # now check
    print('Done, checking results:')
    new_wrk_dir = _read_working_dir(wells_annotations_filename)
    print('New working directory:')
    print(new_wrk_dir)

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
    wrk_dir = ''
    try:
        with h5py.File(wells_annotations_filename, 'r+') as fid:
            wrk_dir = fid["/filenames_df"].attrs["working_dir"]
        # print(wrk_dir)
    except KeyError as ke:
        err_msg = 'Could not read the working directory.\n'
        err_msg += "Original error message: \n"
        err_msg += ke.args[0]
        print(err_msg)
    return wrk_dir


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

# %%
def test():
    data_dir = Path.home() / 'work_repos/WellAnnotator/data'
    for dd in ['MaskedVideos', 'Results']:
        assert _is_child_of_tierpsy_out_dir(data_dir / dd)
        assert check_good_input(data_dir / dd)
        assert tierpsyoutdir2aux(data_dir / dd) == (data_dir / 'AuxiliaryFiles')
        assert get_project_root(data_dir / dd) == data_dir, f'{data_dir / dd}'
        wafname = name_new_wellsanns_file(data_dir / dd)
        assert 'AuxiliaryFiles' in wafname.parts
        assert wafname.name.endswith(WELLS_ANNOTATION_EXT)
        wafname2 = initialise_annotations_file(data_dir / dd)
        assert wafname == wafname2
        assert wafname2.exists()
        wafname2.unlink()

    assert _is_child_of_tierpsy_out_dir(data_dir / 'AuxiliaryFiles') is False
    try:
        check_good_input(data_dir / 'AuxiliaryFiles')
    except AssertionError as e:
        print(data_dir / 'AuxiliaryFiles', e.args[0])


# %%
if __name__ == "__main__":

    test()

    input_str = '/Users/lferiani/work_repos/WellAnnotator/data/Results'
    # input_str = '/Users/lferiani/work_repos/WellAnnotator/data/MaskedVideos/data_20200715_152507_wells_annotations.hdf5'
    annotations_file = get_or_create_annotations_file(input_str)
    # out = ask_if_prestim_only()
    # print(out)





