#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 16 18:51:44 2021

@author: lferiani

Very minimal version of the FOVMultiWellsSplitter class, to decouple this
from Tierpsy
"""

import tables
import numpy as np
import pandas as pd


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

    def tile_FOV(self, img):
        """
        Function that tiles the input image or stack and
        returns a dictionary of (well_name, well_stack).
        """
        assert img.ndim in [2, 3], 'Can only tile 2D or 3D arrays'
        # initialise output
        out_dict = {}
        for _, well in self.wells.iterrows():
            out_dict[well['well_name']] = img[
                ...,  # takes care of img being 2 or 3D
                max(well['y_min'], 0): min(well['y_max'], self.img_shape[0]),
                max(well['x_min'], 0): min(well['x_max'], self.img_shape[1])
                ]
        return out_dict
