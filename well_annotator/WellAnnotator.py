#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 15 16:12:37 2020

@author: lferiani
"""

# TODO: look into opening all the videos from a single plate,
# and allow to move within the plates

import sys
import h5py
import numpy as np
import pandas as pd
import warnings
from tqdm import tqdm
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
    QLabel,
    )

from well_annotator.helper import (
    check_good_input,
    get_or_create_annotations_file,
    get_list_masked_or_feats,
    WELLS_ANNOTATIONS_DF_COLS,
    BUTTON_STYLESHEET_STR,
    BTN_COLOURS,
    WELL_LABELS,
    )
from well_annotator.HDF5VideoPlayer import LineEditDragDrop
from well_annotator.WellsVideoPlayer import WellsVideoPlayerGUI


def _updateUI(ui):

    # second layer
    ui.good_well_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_2.addWidget(ui.good_well_b)
    ui.good_well_b.setText("Good Well")
    ui.good_well_b.setToolTip("Shortcut: 1")

    ui.misaligned_well_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_2.addWidget(ui.misaligned_well_b)
    ui.misaligned_well_b.setText("Misaligned")
    ui.misaligned_well_b.setToolTip("Shortcut: 2")

    ui.precipitation_well_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_2.addWidget(ui.precipitation_well_b)
    ui.precipitation_well_b.setText("Precipitation")
    ui.precipitation_well_b.setToolTip("Shortcut: 3")

    ui.contamination_well_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_2.addWidget(ui.contamination_well_b)
    ui.contamination_well_b.setText("Contamination")
    ui.contamination_well_b.setToolTip("Shortcut: 4")

    ui.wet_well_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_2.addWidget(ui.wet_well_b)
    ui.wet_well_b.setText("Wet Well")
    ui.wet_well_b.setToolTip("Shortcut: 5")

    ui.badagar_well_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_2.addWidget(ui.badagar_well_b)
    ui.badagar_well_b.setText("Bad Agar")
    ui.badagar_well_b.setToolTip("Shortcut: 6")

    ui.otherbad_well_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_2.addWidget(ui.otherbad_well_b)
    ui.otherbad_well_b.setText("Other Bad")
    ui.otherbad_well_b.setToolTip("Shortcut: 7")

    ui.bad_lawn_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_2.addWidget(ui.bad_lawn_b)
    ui.bad_lawn_b.setText("Bad Lawn")
    ui.bad_lawn_b.setToolTip("Shortcut: 8")

    ui.bad_worms_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_2.addWidget(ui.bad_worms_b)
    ui.bad_worms_b.setText("Bad Worms")
    ui.bad_worms_b.setToolTip("Shortcut: 9")

    # third layer
    # add tooltips and a pushbutton to go to next well to review
    ui.next_well_to_review_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_3.insertWidget(2, ui.next_well_to_review_b)
    ui.next_well_to_review_b.setText("Next Well To Review")
    ui.next_well_to_review_b.setToolTip("Shortcut: ]")
    ui.prev_well_b.setToolTip("Shortcut: - or _")
    ui.next_well_b.setToolTip("Shortcut: + or =")

    # fourth layer
    # add tooltip to the pushbutton
    ui.prev_vid_b.setToolTip("Shortcut: ,")
    ui.next_vid_b.setToolTip("Shortcut: .")
    ui.save_b.setToolTip("Shortcut: s")

    # fifth layer
    ui.label_vid_counter = QLabel(ui.centralWidget)
    ui.label_vid_counter.setObjectName("label_vid_counter")
    ui.label_vid_counter.setText("#/##")
    ui.horizontalLayout_5.addWidget(ui.label_vid_counter)

    # add button for running neural network
    ui.run_nn_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_5.addWidget(ui.run_nn_b)
    ui.run_nn_b.setText("Run CNN Classifier")

    # 6th layer add placeholder and a tooltip for the open button
    ui.lineEdit_video.setPlaceholderText(
        "Drag & drop an existing *_wells_annotations.hdf5 file,"
        "a MaskedVideos or Results folder, or one of their day-subfolders."
        )
    ui.pushButton_video.setToolTip("Shortcut: o")

    # add 7th layer
    ui.horizontalLayout_7 = QHBoxLayout()
    ui.horizontalLayout_7.setContentsMargins(11, 11, 11, 11)
    ui.horizontalLayout_7.setSpacing(6)
    ui.horizontalLayout_7.setObjectName("horizontalLayout_7")
    ui.verticalLayout.addLayout(ui.horizontalLayout_7)
    # 7th layer widgets
    ui.rescan_dir_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_7.addWidget(ui.rescan_dir_b)
    ui.rescan_dir_b.setText(
        "Rescan working directory (only adds vids, cannot remove them!!!)")
    ui.checkBox_prestim_only = QCheckBox(ui.centralWidget)
    ui.checkBox_prestim_only.setObjectName("checkbox_prestim_only")
    ui.checkBox_prestim_only.setText("prestim only")
    ui.horizontalLayout_7.addWidget(ui.checkBox_prestim_only)
    ui.checkBox_prestim_only.toggle()
    ui.export_csv_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_7.addWidget(ui.export_csv_b)
    ui.export_csv_b.setText("Export to csv")

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

        self.buttons = {
            1: self.ui.good_well_b,
            2: self.ui.misaligned_well_b,
            3: self.ui.precipitation_well_b,
            4: self.ui.contamination_well_b,  # bacterial/fungal?
            5: self.ui.wet_well_b,
            6: self.ui.badagar_well_b,
            7: self.ui.otherbad_well_b,
            8: self.ui.bad_lawn_b,
            9: self.ui.bad_worms_b,
            }

        # connect ui elements to functions
        LineEditDragDrop(
            self.ui.lineEdit_video,
            self.updateAnnotationsFile,
            self.check_good_input)
        self.ui.pushButton_video.clicked.disconnect()
        self.ui.pushButton_video.clicked.connect(self.getAnnotationsFile)
        self.ui.next_well_to_review_b.clicked.connect(
            self.next_well_to_review)
        self.ui.next_vid_b.clicked.connect(self.next_video_fun)
        self.ui.prev_vid_b.clicked.connect(self.prev_video_fun)
        self.ui.save_b.clicked.connect(self.save_to_disk_fun)
        self.ui.run_nn_b.clicked.connect(self.run_wellclassifier_fun)
        self.ui.rescan_dir_b.clicked.connect(self.rescan_working_dir)
        self.ui.export_csv_b.clicked.connect(self.export_csv_fun)
        # self.ui.checkBox_prestim_only.clicked.connect(self.print_checkBox)
        self._setup_buttons()

        return

    @WellsVideoPlayerGUI.target_frames_to_read.setter
    def target_frames_to_read(self, value):
        self._target_frames_to_read = value
        if self.current_file_id is not None:
            self.updateVideoFile(self.current_file_id)

    def print_checkBox(self):
        "dummy debugging function"
        print(self.ui.checkBox_prestim_only.isChecked())

    def getAnnotationsFile(self):
        print('choosing annotations file')
        annfilename, _ = QFileDialog.getOpenFileName(
            self, "Find HDF5 annotations file", str(self.working_dir),
            "HDF5 files (*wells_annotations.hdf5);; All files (*)")
        print(f'chosen file: {annfilename}')
        if self.check_good_input(annfilename):
            self.updateAnnotationsFile(annfilename)

    def check_good_input(self, annfilename):
        try:
            check_good_input(annfilename)
            return True
        except Exception as e:
            err_msg = e.args[0]
            QMessageBox.critical(self, "Error", err_msg)
            return False

    def updateAnnotationsFile(self, input_path):
        is_prestim_only = self.ui.checkBox_prestim_only.isChecked()
        # get path to annotation file on disk
        try:
            self.wellsanns_file = get_or_create_annotations_file(
                input_path, is_prestim_only=is_prestim_only)
        except Exception as ee:
            err_msg = f"Error:\n{ee.args[0]}"
            QMessageBox.critical(
                self,
                '',
                err_msg,
                QMessageBox.Ok)
            self.wellsanns_file = None
            return

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

        return

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

    def get_next_file_with_unannotated_wells(self, file_id=None):
        """
        return lowest file_id larger than the given file_id (or the current)
        with wells that have not been annotated yet
        """
        # print("finding next file with unannotated wells")
        if file_id is None:
            file_id = self.current_file_id
        # print(f'must be > {file_id}')

        if self.wells_annotations_df.shape[0] == 0:
            # print('no wells annotated yet, go to beginning')
            return 0
        # is this the very last video in the list? if yes, restart
        if file_id == self.filenames_df['file_id'].max():
            # print('already at end of files list, restart from beginning')
            return self.get_first_file_to_process()
        # is this the max file_id in wells_annotations_df?
        # if yes, we just open a new one
        if file_id == self.wells_annotations_df['file_id'].max():
            # we should now be able to go to the next video
            # because I've already checked this is not the last one
            return file_id + 1
        # are there files with wells that have not been annotated yet?
        left_behind = self.get_file_id_with_skipped_wells()
        if len(left_behind) > 0:
            if left_behind.gt(file_id).any():
                # print(f'found {left_behind}')
                next_file_id = left_behind.loc[
                    left_behind.gt(file_id)].min()
            else:
                # print('any file with non annotated wells is behind this one')
                next_file_id = left_behind.min()
            return next_file_id
        # if we get here, there are no files with unannotated wells
        # print('all wells annotated')
        QMessageBox.information(
            self, 'Finished', 'All wells have been annotated.',
            QMessageBox.Ok)
        return 0

    def get_first_file_to_process(self):
        return self.get_next_file_with_unannotated_wells(file_id=-1)

    def get_file_id_with_skipped_wells(self):
        left_behind = self.wells_annotations_df.query(
            'well_label == 0')['file_id']
        return left_behind

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
        tierpsy_fnames = get_list_masked_or_feats(
            self.working_dir, is_prestim_only=is_prestim_only)
        # relative, and string
        tierpsy_fnames = [
            str(f.relative_to(self.working_dir)) for f in tierpsy_fnames]
        # remove the ones that already existed
        new_tierpsy_fnames = list(
            set(tierpsy_fnames) - set(self.filenames_df['filename'].to_list()))
        # check for early exit
        if len(new_tierpsy_fnames) == 0:
            print('No new files found')
            return
        # if new files were found
        n_new_files = len(new_tierpsy_fnames)
        prev_max_id = self.filenames_df['file_id'].max()
        prev_max_index = self.filenames_df.index.max()
        new_file_ids = [prev_max_id + 1 + cc for cc in range(n_new_files)]
        new_index = [prev_max_index + 1 + cc for cc in range(n_new_files)]
        new_filenames_df = pd.DataFrame(
            {'file_id': new_file_ids, 'filename': new_tierpsy_fnames},
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

    # decorator to only run function if an annotation file has been loaded
    def _annotations_loaded_only(func):
        def wrapper(self):
            if self.wellsanns_file is not None:
                return func(self)
            else:
                print('No annotations file loaded')
                return
        return wrapper

    @_annotations_loaded_only
    def next_well_fun(self):
        # these next two lines work, but don't allow me to go to
        # next video when out of wells
        # super().next_well_fun()
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

    @_annotations_loaded_only
    def prev_well_fun(self):
        # super().prev_well_fun()
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

    @_annotations_loaded_only
    def next_well_to_review(self):
        # check that all wells have already been through the NN
        # (or have been manually cycled through)
        # if (len(self.wells_annotations_df) == 0) or (
        #         self.wells_annotations_df['file_id'].max()
        #         < self.filenames_df['file_id'].max()):
        #     # create an error message in a QMessageBox
        #     QMessageBox.critical(
        #         self, '',
        #         'You should run the neural network before reviewing',
        #         QMessageBox.Ok
        #         )

        # find next well to review
        # this is a well that exists in wells_annotations_df but has label 0
        # and is after the current file_id
        # prioritise the next well with label 0 in the open file

        next_well_ind = self._find_index_of_next_well_to_review_in_opened_set()
        # easy case: at least a well to review in the current set
        if next_well_ind is not None:
            self.ui.wells_comboBox.setCurrentIndex(next_well_ind)
            self._refresh_buttons()
            return
        # harder case: no well to review in the current set
        # first we write the current set of annotations into the larger df
        self.store_progress()
        # we need to find (file_id, well_id of next well to review)
        file_id_to_open = self.get_next_file_with_unannotated_wells()
        self.updateVideoFile(file_id_to_open)
        next_well_ind = (
            self._find_index_of_next_well_to_review_in_opened_set(
                current_well_index=-1)
            )
        if next_well_ind is not None:
            self.ui.wells_comboBox.setCurrentIndex(next_well_ind)
            self._refresh_buttons()
        else:
            print('All wells have an annotation')

        return

    def _find_index_of_next_well_to_review_in_opened_set(
            self, current_well_index=None):
        """
        _find_index_of_next_well_to_review_in_opened_set
        find first well in opened set with label 0, returns index to feed
        to wells_comboBox.setCurrentIndex() or None if no such well exists
        """
        if current_well_index is None:
            current_well_index = self.ui.wells_comboBox.currentIndex()
        next_well_ind = None  # only overwritten if I can find a good value
        if self.wells_df['well_label'].eq(0).any():
            # find first well in opened set
            # after the current one with label 0
            iloc_zeros = np.argwhere(
                self.wells_df['well_label'].eq(0).values).ravel()
            iloc_zeros = iloc_zeros[
                iloc_zeros > current_well_index
                ]
            if len(iloc_zeros) > 0:
                next_well_ind = iloc_zeros[0]

        return next_well_ind

    def _refresh_buttons(self,):
        # get current label:
        label_id = self.wells_df.loc[self.well_name, 'well_label']
        if label_id > 0:
            self.buttons[label_id].setChecked(True)
        else:
            for btn in self.buttons.values():
                btn.setChecked(False)
                btn.repaint()

    @_annotations_loaded_only
    def next_video_fun(self):
        next_id = self.current_file_id + 1
        if next_id in self.filenames_df['file_id'].values:
            self.updateVideoFile(next_id)
        return

    @_annotations_loaded_only
    def prev_video_fun(self):
        prev_id = self.current_file_id - 1
        if prev_id in self.filenames_df['file_id'].values:
            self.updateVideoFile(prev_id)
        return

    def keyPressEvent(self, event):
        # read pressed key
        key = event.key()

        # Move to next well when pressed:  = or +
        if key == Qt.Key_Equal or key == Qt.Key_Plus:
            self.next_well_fun()

        # Move to previous well when pressed: - or _
        elif key == Qt.Key_Minus or key == Qt.Key_Underscore:
            self.prev_well_fun()

        # move to next unannotated well when pressed: ] or }
        elif key == Qt.Key_BracketRight or key == Qt.Key_BraceRight:
            self.next_well_to_review()

        # move to next video when pressed > or .
        elif key == Qt.Key_Greater or key == Qt.Key_Period:
            self.next_video_fun()

        # Move to previous video when pressed: < or ,
        elif key == Qt.Key_Less or key == Qt.Key_Comma:
            self.prev_video_fun()

        # open the file selector when pressed: o
        elif key == Qt.Key_O:
            self.getAnnotationsFile()

        else:
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

    @_annotations_loaded_only
    def save_to_disk_fun(self):
        self.store_progress()
        warnings.simplefilter(
            action='ignore',
            category=pd.errors.PerformanceWarning
            )
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

    @_annotations_loaded_only
    def export_csv_fun(self):
        self.store_progress()
        # prepare a single spreadsheet
        out_df = pd.merge(
            left=self.filenames_df,
            right=self.wells_annotations_df,
            on='file_id',
            how='right',
            validate='1:m',
            sort=False)
        # add the working directory
        out_df['filename'] = f'{self.working_dir}/' + out_df['filename']
        # add an explanation for the labels
        out_df['label_meaning'] = out_df['well_label'].map(WELL_LABELS)
        out_df['label_meaning'].fillna(value='not annotated', inplace=True)
        # extract the imgstore name, if all files are indeed from loopbio
        if out_df['filename'].apply(
                lambda x: 'metadata' in Path(x).name).all():
            out_df.insert(
                loc=2,
                column='imgstore_name',
                value=out_df['filename'].apply(lambda x: Path(x).parent.name))
        # do some checks
        warn_msg = ''
        if out_df['well_label'].isin([0]).any():
            warn_msg += 'Some wells were not annotated!\n'
        if (~self.filenames_df['file_id'].isin(out_df['file_id'])).any():
            warn_msg += 'Not all videos have been annotated!\n'
        if len(warn_msg) > 0:
            warn_msg += '\nDo you want to export anyway?'

            reply = QMessageBox.question(
                self,
                'Warning',
                warn_msg,
                QMessageBox.No | QMessageBox.Yes,
                QMessageBox.Yes)
            if reply != QMessageBox.Yes:
                return

        # create out name
        out_fname = self.wellsanns_file.with_suffix('.csv')
        # save
        out_df.drop(columns=['file_id']).to_csv(out_fname, index=False)
        print(f'csv exported to {out_fname}')
        return

    @_annotations_loaded_only
    def run_wellclassifier_fun(self):
        """
        run_wellclassifier_fun
        Use trained classifier(s) to automatically classify wells as good
        or bad. Wells predicted to be good will be marked as such, while
        wells predicted to be bad will be left unannotated for the user to
        review.
        """
        from well_annotator.helper import (
            load_CNN_models, preprocess_images_for_CNN, majority_vote)

        is_skip_existing_annotations = False
        if len(self.wells_annotations_df) > 0:
            warn_msg = (
                "Existing annotations detected.\n"
                "Overwrite the existing annotations?"
                )
            reply = QMessageBox.question(
                self, 'Warning', warn_msg,
                QMessageBox.No | QMessageBox.Yes, QMessageBox.Yes)

            if (reply == QMessageBox.No) and (
                    self.wells_annotations_df['well_label'].eq(0).any()):
                warn_msg = "Would you like to classify the unannotated wells?"
                reply = QMessageBox.question(
                    self, 'Warning', warn_msg,
                    QMessageBox.No | QMessageBox.Yes, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    is_skip_existing_annotations = True
                else:
                    print('Nothing done, exiting')
                    return
            else:
                print('Nothing done, exiting')
                return


        # load the model
        models = load_CNN_models()

        # let's make sure we're at the very beginning
        self.updateVideoFile(0)
        # loop through all the wells using self.next_well_fun()
        # as it allows to move through videos as well
        # The end of the loop is detected as file id and well name dont change
        pbar = tqdm(desc='files processed', total=len(self.filenames_df))
        last_file_well = (None, None)
        while last_file_well != (self.current_file_id, self.well_name):
            # update progress bar and store progress whenever we change file id
            if self.current_file_id != last_file_well[0]:
                pbar.update(n=1)
                self.save_to_disk_fun()

            # skip the classification if we asked not to overwrite
            if is_skip_existing_annotations:
                if self.wells_df.loc[self.well_name, 'well_label'] != 0:
                    last_file_well = (self.current_file_id, self.well_name)
                    self.next_well_fun()
                    continue

            # classify the well's images
            images = preprocess_images_for_CNN(self.image_group)
            well_prediction = majority_vote(models, images)

            # NN predicts 1 if it's bad well, 0 if it is good
            # translate prediction into label (good well, unannotated if bad)
            if well_prediction == 0:
                self.wells_df.loc[self.well_name, 'well_label'] = 1
            else:
                self.wells_df.loc[self.well_name, 'well_label'] = 0

            # update last_file_well and move to next well
            last_file_well = (self.current_file_id, self.well_name)
            self.next_well_fun()

        self.save_to_disk_fun()

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


def launch_app():
    app = QApplication(sys.argv)
    ui = WellsAnnotator()
    ui.show()
    sys.exit(app.exec_())


# def main():
#     import fire
#     fire.Fire(launch_app)


if __name__ == '__main__':
    launch_app()
