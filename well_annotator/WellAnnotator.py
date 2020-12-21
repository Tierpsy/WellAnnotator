#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 15 16:12:37 2020

@author: lferiani
"""

# TODO: look into opening all the videos from a single plate, and allow to move within the plates

import sys
import h5py
import pandas as pd

from pathlib import Path
from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QCheckBox,
    QLabel)

from helper import (
    check_good_input,
    get_or_create_annotations_file,
    get_list_masked_videos,
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

    # 6th layer unmodified

    # add 7th layer
    ui.horizontalLayout_7 = QHBoxLayout()
    ui.horizontalLayout_7.setContentsMargins(11, 11, 11, 11)
    ui.horizontalLayout_7.setSpacing(6)
    ui.horizontalLayout_7.setObjectName("horizontalLayout_7")
    ui.verticalLayout.addLayout(ui.horizontalLayout_7)
    # 7th layer widgets
    ui.rescan_dir_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_7.addWidget(ui.rescan_dir_b)
    ui.rescan_dir_b.setText("Rescan working directory")
    ui.checkBox_prestim_only = QCheckBox(ui.centralWidget)
    ui.checkBox_prestim_only.setObjectName("checkbox_prestim_only")
    ui.checkBox_prestim_only.setText("prestim only")
    ui.horizontalLayout_7.addWidget(ui.checkBox_prestim_only)
    ui.checkBox_prestim_only.toggle()

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
                        4: self.ui.contamination_well_b, # bacterial/fungal?
                        5: self.ui.wet_well_b,
                        6: self.ui.badagar_well_b,
                        7: self.ui.otherbad_well_b}

        # connect ui elements to functions
        LineEditDragDrop(
            self.ui.lineEdit_video,
            self.updateAnnotationsFile,
            check_good_input)
        self.ui.pushButton_video.clicked.disconnect()
        self.ui.pushButton_video.clicked.connect(self.getAnnotationsFile)
        self.ui.next_vid_b.clicked.connect(self.next_video_fun)
        self.ui.prev_vid_b.clicked.connect(self.prev_video_fun)
        self.ui.save_b.clicked.connect(self.save_to_disk_fun)
        self.ui.rescan_dir_b.clicked.connect(self.rescan_working_dir)
        # self.ui.checkBox_prestim_only.clicked.connect(self.print_checkBox)
        self._setup_buttons()

        return

    def print_checkBox(self):
        "dummy debugging function"
        print(self.ui.checkBox_prestim_only.isChecked())

    def getAnnotationsFile(self):
        print('choosing annotations file')
        annfilename, _ = QFileDialog.getOpenFileName(
            self, "Find HDF5 annotations file", str(self.working_dir),
            "HDF5 files (*wells_annotations.hdf5);; All files (*)")
        _ = check_good_input(annfilename)
        self.updateAnnotationsFile(annfilename)

    def updateAnnotationsFile(self, input_path):
        is_prestim_only = self.ui.checkBox_prestim_only.isChecked()
        # get path to annotation file on disk
        self.wellsanns_file = get_or_create_annotations_file(
            input_path, is_prestim_only=is_prestim_only)
        # read its content
        with pd.HDFStore(self.wellsanns_file) as fid:
            self.filenames_df = fid['/filenames_df'].copy()
            self.working_dir = Path(
                fid.get_storer('filenames_df').attrs.working_dir)
            self.wells_annotations_df = fid['/wells_annotations_df'].copy()

        self.ui.lineEdit_video.setText(str(self.wellsanns_file))

        # if loading a hdf5 with other than prestim vids,
        # set is_prestim false and disable checkBox_prestim_only
        if not all(self.filenames_df['filename'].str.contains('prestim')):
            self.ui.checkBox_prestim_only.setChecked(False)
            self.ui.checkBox_prestim_only.setEnabled(False)
            print('set prestim only false')

        file_id_to_open = self.get_first_file_to_process()
        self.updateVideoFile(file_id_to_open)

        pass

    def updateVideoFile(self, file_id_to_open):
        # print(f'file_id before updating: {self.current_file_id})')
        # store the previous video's annotations in self.wells_annotations_df
        if self.wells_df is not None:
            self.store_progress()
        # get the name of the next video to open
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
            if ind.any():
                left_behind = self.wells_annotations_df[ind]
                return left_behind['file_id'].min()
            else:
                new_file_id = self.wells_annotations_df['file_id'].max() + 1
                if new_file_id in self.filenames_df['file_id'].values:
                    return new_file_id
                else:
                    return 0

    def get_vfilename_from_file_id(self, file_id_to_open):
        try:
            fname = self.filenames_df.set_index(
                'file_id').loc[file_id_to_open, 'filename']
        except Exception as EE:
            print(f'Failed to find filename of file_id {file_id_to_open}')
            print('This is how self.filenames_df look like:')
            print(self.filenames_df)
            print('Details of the exception:')
            print(type(EE))    # the exception instance
            print(EE.args)     # arguments stored in .args
            print(EE)
            raise
        fname = self.working_dir / fname
        fname = str(fname)
        return fname

    def rescan_working_dir(self):
        """
        Scan the working_dir, add any new files to the filenames_df DataFrame.
        If is_prestim_only is unchecked, this will add all the non-prestim
        videos as well!
        """
        # do nothing if you click it before loading a video!
        if self.working_dir is None:
            return
        # find all masked videos in working_dir (accounting for prestim flag)
        is_prestim_only = self.ui.checkBox_prestim_only.isChecked()
        masked_fnames = get_list_masked_videos(
            self.working_dir, is_prestim_only=is_prestim_only)
        # relative, and string
        masked_fnames = [
            str(f.relative_to(self.working_dir)) for f in masked_fnames]
        # remove the ones that already existed
        new_masked_fnames = list(
            set(masked_fnames) - set(self.filenames_df['filename'].to_list()))
        # check for early exit
        if len(new_masked_fnames) == 0:
            print('No new files found')
            return
        # if new files were found
        n_new_files = len(new_masked_fnames)
        prev_max_id = self.filenames_df['file_id'].max()
        prev_max_index = self.filenames_df.index.max()
        new_file_ids = [prev_max_id + 1 + cc for cc in range(n_new_files)]
        new_index = [prev_max_index + 1 + cc for cc in range(n_new_files)]
        new_filenames_df = pd.DataFrame(
            {'file_id': new_file_ids, 'filename': new_masked_fnames},
            index=new_index
            )
        print(f'{n_new_files} new files found')
        self.filenames_df = pd.concat(
            [self.filenames_df, new_filenames_df], axis=0)

        self.updateVideoFile(self.current_file_id)

        return

    def store_progress(self):
        """
        add wells_df to self.wells_annotations_df
        """
        # easy case: this is the first time we see these wells
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
            idx = self.wells_annotations_df['file_id'] == self.current_file_id
            # next line assumes wells order not to have changed
            # since wells_df was first appendsed. sounds reasonable enough
            assert all(
                (self.wells_annotations_df.loc[idx, 'well_name'].values
                 == self.wells_df.reset_index()['well_name'].values)
                ), 'wells order not matching'
            self.wells_annotations_df.loc[idx, 'well_label'] = (
                self.wells_df['well_label'].values)
        return

    def nextWell_fun(self):
        # these next two lines work, but don't allow me to go to
        # next video when out of wells
        # super().nextWell_fun()
        # self._refresh_buttons()
        nwells = self.ui.wells_comboBox.count()
        if self.ui.wells_comboBox.currentIndex() < (nwells - 1):
            # increase index
            self.ui.wells_comboBox.setCurrentIndex(
                self.ui.wells_comboBox.currentIndex() + 1)
        else:
            self.next_video_fun()
        self._refresh_buttons()
        return

    def prevWell_fun(self):
        # super().prevWell_fun()
        # self._refresh_buttons()
        if self.ui.wells_comboBox.currentIndex() > 0:
            self.ui.wells_comboBox.setCurrentIndex(
                self.ui.wells_comboBox.currentIndex() - 1)
        else:
            self.prev_video_fun()
            # go to last well of previous video
            self.ui.wells_comboBox.setCurrentIndex(
                self.ui.wells_comboBox.count() - 1)
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
        # read pressed key
        key = event.key()
        # toggle the right button
        for btn_id, btn in self.buttons.items():
            if key == (Qt.Key_0+btn_id):
                btn.toggle()
                # print(WELL_LABELS[btn_id])
                return
        return

    def _setup_buttons(self):
        """
        Control button appearance and behaviour
        """
        stylesheet_str = BUTTON_STYLESHEET_STR

        # function called when a button is activated
        def _make_label(label_id, checked):
            """
            if function called when checking a button,
            loop through all the other buttons and uncheck those.
            And set well's label to be this checked button.'
            If unchecking a checked button, delete the existing annotation"""
            if checked:
                for btn_id, btn in self.buttons.items():
                    if btn_id != label_id:
                        btn.setChecked(False)
                    btn.repaint()

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
        # connect ui elements to callback function
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
        self.filenames_df.to_hdf(
            self.wellsanns_file,
            key='/filenames_df',
            index=False,
            mode='r+')
        # add working_dir
        with h5py.File(self.wellsanns_file, 'r+') as fid:
            fid["/filenames_df"].attrs["working_dir"] = str(self.working_dir)
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
