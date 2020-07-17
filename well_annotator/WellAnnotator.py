#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 15 16:12:37 2020

@author: lferiani
"""

import sys
import pandas as pd

from pathlib import Path
from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QPushButton,
    QMessageBox,
    QLabel)

from helper import (
    check_good_input, get_or_create_annotations_file,
    WELLS_ANNOTATIONS_DF_COLS,
    BUTTON_STYLESHEET_STR,
    BTN_COLOURS,
    )
from HDF5VideoPlayer import LineEditDragDrop
from WellsVideoPlayer import WellsVideoPlayerGUI


def _updateUI(ui):

    # second layer
    ui.good_well_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_2.addWidget(ui.good_well_b)
    ui.good_well_b.setText("Good Well")

    ui.misaligned_well_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_2.addWidget(ui.misaligned_well_b)
    ui.misaligned_well_b.setText("Misaligned")

    ui.precipitation_well_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_2.addWidget(ui.precipitation_well_b)
    ui.precipitation_well_b.setText("Precipitation")

    ui.contamination_well_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_2.addWidget(ui.contamination_well_b)
    ui.contamination_well_b.setText("Contamination")

    ui.wet_well_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_2.addWidget(ui.wet_well_b)
    ui.wet_well_b.setText("Wet Well")

    ui.badagar_well_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_2.addWidget(ui.badagar_well_b)
    ui.badagar_well_b.setText("Bad Agar")

    ui.otherbad_well_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_2.addWidget(ui.otherbad_well_b)
    ui.otherbad_well_b.setText("Other Bad")

    # fifth layer
    ui.label_vid_counter = QLabel(ui.centralWidget)
    ui.label_vid_counter.setObjectName("label_vid_counter")
    ui.label_vid_counter.setText("#/##")
    ui.horizontalLayout_5.addWidget(ui.label_vid_counter)

    return ui


class WellsAnnotator(WellsVideoPlayerGUI):

    def __init__(self, ui=None):

        super().__init__()
        self.ui = _updateUI(self.ui)

        # properties
        self.wellsanns_file = None
        self.filenames_df = None
        self.working_dir = None
        self.wells_annotations_df = None
        self.current_file_id = None

        self.buttons = {1: self.ui.good_well_b,
                        2: self.ui.misaligned_well_b,
                        3: self.ui.precipitation_well_b,
                        4: self.ui.contamination_well_b,
                        5: self.ui.wet_well_b,
                        6: self.ui.badagar_well_b,
                        7: self.ui.otherbad_well_b}

        LineEditDragDrop(
            self.ui.lineEdit_video,
            self.updateAnnotationsFile,
            check_good_input)

        # connect ui elements to functions
        self.ui.next_vid_b.clicked.connect(self.next_video_fun)
        self.ui.prev_vid_b.clicked.connect(self.prev_video_fun)
        self.ui.save_b.clicked.connect(self.save_to_disk_fun)
        self._setup_buttons()

        return

    def updateAnnotationsFile(self, input_path):
        # get path to annotation file on disk
        self.wellsanns_file = get_or_create_annotations_file(input_path)
        # read its content
        with pd.HDFStore(self.wellsanns_file) as fid:
            self.filenames_df = fid['/filenames_df'].copy()
            self.working_dir = Path(
                fid.get_storer('filenames_df').attrs.working_dir)
            self.wells_annotations_df = fid['/wells_annotations_df'].copy()
        # print(self.wellsanns_file)
        # print(self.filenames_df)
        # print(self.filenames_df['file_id'].min())
        # print(self.wells_annotations_df)

        self.ui.lineEdit_video.setText(str(self.wellsanns_file))

        file_id_to_open = self.get_first_file_to_process()
        self.updateVideoFile(file_id_to_open)

        pass

    def updateVideoFile(self, file_id_to_open):
        # print(f'file_id before updating: {self.current_file_id})')
        # store the previous video's annotations in self.wells_annotations_df
        if self.wells_df is not None:
            # print('temp storing progress')
            self.store_progress()
        # else:
            # print('no progress to store yet')
        vfile_to_open = self.get_vfilename_from_file_id(file_id_to_open)
        # use WellsVideoPlayer's
        super().updateVideoFile(vfile_to_open)
        self.current_file_id = file_id_to_open
        # but then overwrite the self.wells_df in case this file had already
        # been annotated to a certain extent
        if self.current_file_id in self.wells_annotations_df['file_id'].values:
            self.wells_df = self.wells_annotations_df.query(
                f'file_id == {self.current_file_id}').set_index('well_name')
        else:
            # add labels column
            self.wells_df['well_label'] = 0
            self.wells_df['file_id'] = self.current_file_id
        # print(f'file_id after updating: {self.current_file_id})')
        # update ui elements
        self.ui.label_vid_counter.setText(
            (f'{self.current_file_id+1}/'
             + f'{len(self.filenames_df)}'))
        self._refresh_buttons()
        return

    def get_first_file_to_process(self):
        if self.wells_annotations_df.shape[0] == 0:
            return 0
        else:
            ind = self.wells_annotations_df['well_label'] == 0
            left_behind = self.wells_annotations_df[ind]
            return left_behind['file_id'].min()

    def get_vfilename_from_file_id(self, file_id):
        fname = self.working_dir / self.filenames_df.loc[file_id, 'filename']
        fname = str(fname)
        return fname

    def store_progress(self):
        """
        add wells_df to self.wells_annotations_df
        """
        # easy case: this is the first time we see these wells
        # print(f'check if {self.current_file_id} is in ')
        # print(self.wells_annotations_df['file_id'])
        if (self.current_file_id
                not in self.wells_annotations_df['file_id'].values):
            # print('appending')
            self.wells_annotations_df = self.wells_annotations_df.append(
                self.wells_df.reset_index(
                    drop=False
                    )[WELLS_ANNOTATIONS_DF_COLS],
                ignore_index=True,
                verify_integrity=True,
                sort=True
                )
        else:
            # these wells were seen before. update them
            # print('updating')
            idx = self.wells_annotations_df['file_id'] == self.current_file_id
            # next line assumes wells order not to have changed
            # since wells_df was first appendsed. sounds reasonable enough
            assert all(
                (self.wells_annotations_df.loc[idx, 'well_name'].values
                 == self.wells_df.reset_index()['well_name'].values)
                ), 'wells order not matching'
            self.wells_annotations_df.loc[idx, 'well_label'] = (
                self.wells_df['well_label'].values)
        # print('wells_annotations_df:')
        # print(self.wells_annotations_df)
        return

    def nextWell_fun(self):
        super().nextWell_fun()
        self._refresh_buttons()
        return

    def prevWell_fun(self):
        super().prevWell_fun()
        self._refresh_buttons()
        return

    def _refresh_buttons(self,):
        # get current label:
        label_id = self.wells_df.loc[self.well_name, 'well_label']
        if label_id > 0:
            self.buttons[label_id].setChecked(True)
        else:
            for btn in self.buttons.values():
                btn.setChecked(False)
                btn.repaint()

    def next_video_fun(self):
        next_id = self.current_file_id + 1
        if next_id in self.filenames_df['file_id'].values:
            self.updateVideoFile(next_id)
        return

    def prev_video_fun(self):
        prev_id = self.current_file_id - 1
        if prev_id in self.filenames_df['file_id'].values:
            self.updateVideoFile(prev_id)
        return

    def keyPressEvent(self, event):

        key = event.key()
        # print(key)

        for btn_id, btn in self.buttons.items():
            if key == (Qt.Key_0+btn_id):
                btn.toggle()
                # print(WELL_LABELS[btn_id])
                return
        return

    def _setup_buttons(self):
        stylesheet_str = BUTTON_STYLESHEET_STR

        def _make_label(label_id, checked):
            if checked:
                for btn_id, btn in self.buttons.items():
                    if btn_id != label_id:
                        btn.setChecked(False)

            if self.wells_df is not None:
                # find well index
                if checked:
                    # add label
                    self.wells_df.loc[self.well_name, 'well_label'] = label_id
                else:
                    old_lab = self.wells_df.loc[self.well_name, 'well_label']
                    if old_lab == label_id:
                        # if the labeld was unchecked remove the label
                        self.wells_df.loc[self.well_name, 'well_label'] = 0
                # print(self.wells_df)

        for btn_id, btn in self.buttons.items():
            btn.setCheckable(True)
            btn.setStyleSheet(stylesheet_str % BTN_COLOURS[btn_id])
            btn.toggled.connect(partial(_make_label, btn_id))
        return

    def save_to_disk_fun(self):
        self.store_progress()
        self.wells_annotations_df.to_hdf(
            self.wellsanns_file,
            key='/wells_annotations_df',
            index=False,
            mode='r+')
        return

    def closeEvent(self, event):
        quit_msg = "Do you want to save the current progress before exiting?"
        reply = QMessageBox.question(
            self,
            'Message',
            quit_msg,
            QMessageBox.No | QMessageBox.Yes,
            QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            self.save_to_disk_fun()

        super().closeEvent(event)
        return


if __name__ == '__main__':
    app = QApplication(sys.argv)

    ui = WellsAnnotator()
    ui.show()

    sys.exit(app.exec_())
