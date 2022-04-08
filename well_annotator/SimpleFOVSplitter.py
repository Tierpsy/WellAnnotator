#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 16 18:51:44 2021

@author: lferiani

Very minimal version of the FOVMultiWellsSplitter class, to decouple this
from Tierpsy
"""

import cv2
import tables
import numpy as np
import pandas as pd
from collections import OrderedDict


WELLS_COLS = [
    'x', 'y', 'r', 'row', 'col',
    'x_min', 'x_max', 'y_min', 'y_max',
    'well_name', 'is_good_well'
    ]


class SimpleFOVSplitter(object):
    """
    Class tasked with reading the information about splitting the FOV
    into wells, and providing a quick method to split
    an image or stack of images accordingly
    """

    def __init__(self, hdf5_filename):

        # read wells dataframe, handle error
        try:
            self.wells = pd.read_hdf(hdf5_filename, '/fov_wells')
        except KeyError as e:
            msg = 'Could not find the wells information in the file!'
            raise KeyError(msg) from e

        # add all columns we'll need later
        assert all(col in WELLS_COLS for col in self.wells), (
            'Unknown column in /fov_wells')
        # self.wells = self.wells.reindex(columns=WELLS_COLS)
        # self.wells['x'] = 0.5 * (self.wells['x_min'] + self.wells['x_max'])
        # self.wells['y'] = 0.5 * (self.wells['y_min'] + self.wells['y_max'])
        # self.wells['r'] = self.wells['x_max'] - self.wells['x']

        # read extra useful info
        with tables.File(hdf5_filename, 'r') as fid:
            self.img_shape = fid.get_node('/fov_wells')._v_attrs['img_shape']
            if 'is_dubious' in fid.get_node('/fov_wells')._v_attrs:
                if fid.get_node('/fov_wells')._v_attrs['is_dubious']:
                    print(f'Check {hdf5_filename} for plate alignment')

    # def tile_FOV(self, img):
    #     """
    #     Function that tiles the input image or stack and
    #     returns a dictionary of (well_name, well_stack).
    #     """
    #     assert img.ndim in [2, 3], 'Can only tile 2D or 3D arrays'
    #     # initialise output
    #     out_dict = {}
    #     for _, well in self.wells.iterrows():
    #         out_dict[well['well_name']] = img[
    #             ...,  # takes care of img being 2 or 3D
    #             max(well['y_min'], 0): min(well['y_max'], self.img_shape[0]),
    #             max(well['x_min'], 0): min(well['x_max'], self.img_shape[1])
    #             ]
    #     return out_dict

    def tile_FOV(self, img):
        """
        Function that tiles the input image or stack and
        returns a dictionary of (well_name, well_stack).
        """
        assert img.ndim in [2, 3], 'Can only tile 2D or 3D arrays'
        if img.ndim == 2:
            was_2D = True
            img = img[None, ...]
        else:
            was_2D = False

        # check if we need padding
        if self.wells['x_max'].max() > img.shape[2]:
            right_pad = self.wells['x_max'].max() - img.shape[2]
            args = [0, 0, 0, right_pad, cv2.BORDER_REPLICATE]
            img = np.concatenate(
                [cv2.copyMakeBorder(_im, *args)[None, ...] for _im in img])

        if self.wells['y_max'].max() > img.shape[1]:
            bottom_pad = self.wells['y_max'].max() - img.shape[1]
            args = [0, bottom_pad, 0, 0, cv2.BORDER_REPLICATE]
            img = np.concatenate(
                [cv2.copyMakeBorder(_im, *args)[None, ...] for _im in img])

        if self.wells['x_min'].min() < 0:
            left_pad = - self.wells['x_min'].min()
            args = [0, 0, left_pad, 0, cv2.BORDER_REPLICATE]
            img = np.concatenate(
                [cv2.copyMakeBorder(_im, *args)[None, ...] for _im in img])
            self.wells['x_min'] = self.wells['x_min'] + left_pad

        if self.wells['y_min'].min() < 0:
            top_pad = - self.wells['y_min'].min()
            args = [top_pad, 0, 0, 0, cv2.BORDER_REPLICATE]
            img = np.concatenate(
                [cv2.copyMakeBorder(_im, *args)[None, ...] for _im in img])
            self.wells['y_min'] = self.wells['y_min'] + top_pad

        if was_2D:
            img = img[0]

        # initialise output
        out_dict = OrderedDict()
        for _, well in self.wells.iterrows():
            out_dict[well['well_name']] = img[
                ...,
                well['y_min']:well['y_max'],
                well['x_min']:well['x_max']
                ]

        return out_dict

