#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 31 17:22:23 2022

@author: lferiani
"""

from pathlib import Path

base_path = Path(__file__).parent
trained_models_path = base_path / 'trained_models'
# BINARY_MODEL_PATH = trained_models_path / 'v_06_60_20210802_192216.pth'
# MULTICLASS_MODEL_PATH = trained_models_path / 'v_12_63_20210802_192250.pth'

repo_path = base_path.parent
# MANUAL_ANNOTATIONS_PATH = repo_path / 'data'
# DL_DATASET_PATH = MANUAL_ANNOTATIONS_PATH / 'DL_datasets'

# WELL_LABELS = {
#     1: 'good',
#     2: 'misaligned',
#     3: 'precipitation',
#     4: 'contamination',
#     5: 'wet',
#     6: 'bad agar',
#     7: 'other bad',
#     8: 'bad lawns',
#     9: 'bad worms',
#     }
