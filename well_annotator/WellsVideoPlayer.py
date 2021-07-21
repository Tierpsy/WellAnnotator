#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 26 16:13:32 2020

@author: lferiani
"""
import sys
import tables
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QLabel, QPushButton, QComboBox, QHBoxLayout)
# from PyQt.QtWidgets import QCheckBox, QMessageBox

from well_annotator.HDF5VideoPlayer import HDF5VideoPlayerGUI

from tierpsy.analysis.split_fov.FOVMultiWellsSplitter import (
    FOVMultiWellsSplitter)


def _updateUI(ui):

    # delete things
    ui.horizontalLayout_6.removeWidget(ui.pushButton_h5groups)
    ui.pushButton_h5groups.deleteLater()
    ui.pushButton_h5groups = None

    ui.horizontalLayout_3.removeWidget(ui.doubleSpinBox_fps)
    ui.doubleSpinBox_fps.deleteLater()
    ui.doubleSpinBox_fps = None

    ui.horizontalLayout_3.removeWidget(ui.label_frame)
    ui.label_frame.deleteLater()
    ui.label_frame = None

    ui.horizontalLayout_3.removeWidget(ui.label_fps)
    ui.label_fps.deleteLater()
    ui.label_fps = None

    ui.horizontalLayout_3.removeWidget(ui.playButton)
    ui.playButton.deleteLater()
    ui.playButton = None

    ui.horizontalLayout_3.removeWidget(ui.spinBox_step)
    ui.spinBox_step.deleteLater()
    ui.spinBox_step = None

    ui.horizontalLayout_3.removeWidget(ui.label_step)
    ui.label_step.deleteLater()
    ui.label_step = None

    ui.horizontalLayout_6.removeWidget(ui.comboBox_h5path)
    ui.comboBox_h5path.deleteLater()
    ui.comboBox_h5path = None

    # Remove all layouts
    ui.horizontalLayout.deleteLater()
    ui.horizontalLayout = None
    ui.horizontalLayout_2.deleteLater()
    ui.horizontalLayout_2 = None
    ui.horizontalLayout_3.deleteLater()
    ui.horizontalLayout_3 = None
    ui.horizontalLayout_6.deleteLater()
    ui.horizontalLayout_6 = None

    # define layouts
    ui.horizontalLayout = QHBoxLayout()
    ui.horizontalLayout.setContentsMargins(11, 11, 11, 11)
    ui.horizontalLayout.setSpacing(6)
    ui.horizontalLayout.setObjectName("horizontalLayout")
    ui.verticalLayout.addLayout(ui.horizontalLayout)

    ui.horizontalLayout_2 = QHBoxLayout()
    ui.horizontalLayout_2.setContentsMargins(11, 11, 11, 11)
    ui.horizontalLayout_2.setSpacing(6)
    ui.horizontalLayout_2.setObjectName("horizontalLayout_2")
    ui.verticalLayout.addLayout(ui.horizontalLayout_2)

    ui.horizontalLayout_3 = QHBoxLayout()
    ui.horizontalLayout_3.setContentsMargins(11, 11, 11, 11)
    ui.horizontalLayout_3.setSpacing(6)
    ui.horizontalLayout_3.setObjectName("horizontalLayout_3")
    ui.verticalLayout.addLayout(ui.horizontalLayout_3)

    ui.horizontalLayout_4 = QHBoxLayout()
    ui.horizontalLayout_4.setContentsMargins(11, 11, 11, 11)
    ui.horizontalLayout_4.setSpacing(6)
    ui.horizontalLayout_4.setObjectName("horizontalLayout_4")
    ui.verticalLayout.addLayout(ui.horizontalLayout_4)

    ui.horizontalLayout_5 = QHBoxLayout()
    ui.horizontalLayout_5.setContentsMargins(11, 11, 11, 11)
    ui.horizontalLayout_5.setSpacing(6)
    ui.horizontalLayout_5.setObjectName("horizontalLayout_5")
    ui.verticalLayout.addLayout(ui.horizontalLayout_5)

    ui.horizontalLayout_6 = QHBoxLayout()
    ui.horizontalLayout_6.setContentsMargins(11, 11, 11, 11)
    ui.horizontalLayout_6.setSpacing(6)
    ui.horizontalLayout_6.setObjectName("horizontalLayout_6")
    ui.verticalLayout.addLayout(ui.horizontalLayout_6)

    # place widgets:
    # first layer
    ui.horizontalLayout_3.removeWidget(ui.spinBox_frame)
    ui.horizontalLayout.addWidget(ui.spinBox_frame)

    ui.horizontalLayout_2.removeWidget(ui.imageSlider)
    ui.horizontalLayout.addWidget(ui.imageSlider)

    ui.horizontalLayout_2.removeWidget(ui.playButton)
    ui.horizontalLayout.addWidget(ui.playButton)

    # third layer
    ui.prev_well_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_3.addWidget(ui.prev_well_b)
    ui.prev_well_b.setText("Prev Well")

    ui.next_well_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_3.addWidget(ui.next_well_b)
    ui.next_well_b.setText("Next Well")

    ui.wells_comboBox = QComboBox(ui.centralWidget)
    ui.wells_comboBox.setEditable(False)
    ui.wells_comboBox.setObjectName("wells_comboBox")
    ui.wells_comboBox.addItem("")
    ui.horizontalLayout_3.addWidget(ui.wells_comboBox)

    ui.label_well = QLabel(ui.centralWidget)
    ui.label_well.setObjectName("label_well")
    ui.label_well.setText("well name: ")
    ui.horizontalLayout_3.addWidget(ui.label_well)

    ui.label_well_counter = QLabel(ui.centralWidget)
    ui.label_well_counter.setObjectName("label_well_counter")
    ui.label_well_counter.setText("#/##")
    ui.horizontalLayout_3.addWidget(ui.label_well_counter)

    # fourth layer
    ui.prev_vid_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_4.addWidget(ui.prev_vid_b)
    ui.prev_vid_b.setText("Prev Video")

    ui.next_vid_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_4.addWidget(ui.next_vid_b)
    ui.next_vid_b.setText("Next Video")

    ui.save_b = QPushButton(ui.centralWidget)
    ui.horizontalLayout_4.addWidget(ui.save_b)
    ui.save_b.setText("Save")

    # fifth layer
    ui.label_vid = QLabel(ui.centralWidget)
    ui.label_vid.setObjectName("label_vid")
    ui.label_vid.setText("video_name")
    ui.horizontalLayout_5.addWidget(ui.label_vid)

    # ui.horizontalLayout.removeWidget(ui.lineEdit_video)
    ui.horizontalLayout_6.addWidget(ui.lineEdit_video)

    ui.horizontalLayout.removeWidget(ui.pushButton_video)
    ui.horizontalLayout_6.addWidget(ui.pushButton_video)

    return ui


class WellsVideoPlayerGUI(HDF5VideoPlayerGUI):

    def __init__(self, ui=None):

        super().__init__()

        # Set up the user interface
        self.ui = _updateUI(self.ui)

        self.imgstore_name = ''
        self.fovsplitter = None
        self.well_name = ''
        self.tiles = None
        self.well_names = []
        self.wells_df = None  # current video's

        self.frame_number = 0
        self.min_frame = 0
        self.tot_frames = 50
        self.ui.spinBox_frame.setMaximum(self.tot_frames - 1)
        self.ui.imageSlider.setMaximum(self.tot_frames - 1)

        self.ui.wells_comboBox.activated.connect(self.updateImGroup)
        self.ui.wells_comboBox.currentIndexChanged.connect(self.updateImGroup)
        # self.ui.wells_comboBox.activated.connect(self.updateImGroup)

        self.ui.next_well_b.clicked.connect(self.next_well_fun)
        self.ui.prev_well_b.clicked.connect(self.prev_well_fun)

        self.mainImage._view.wheelEvent = self.do_nothing

    def do_nothing(self, event):
        pass

    def wheelEvent(self, event):
        delta = event.pixelDelta().y()
        # -1, 0, +1, cool syntax:
        delta = delta and delta // abs(delta)
        current = self.frame_number
        candidate = max(min(current + delta, self.tot_frames), 0)
        self.ui.spinBox_frame.setValue(candidate)
        return

    def keyPressEvent(self, event):
        print(self.vfilename)

    def updateVideoFile(self, vfilename):

        # close the if there was another file opened before.
        if self.fid is not None:
            self.fid.close()
            self.mainImage.cleanCanvas()
            self.fid = None
            self.image_group = None
            self.imgstore_name = ''
            self.fovsplitter = None
            self.well_name = ''
            self.well_names = []
            self.tiles = None
            self.ui.wells_comboBox.clear()
            self.wells_df = None

        self.vfilename = vfilename
        self.imgstore_name = Path(vfilename).parent.name
        self.ui.label_vid.setText(self.imgstore_name)
        # self.videos_dir = self.vfilename.rpartition(os.sep)[0] + os.sep

        # try:
        #     with tables.File(vfilename, 'r') as fid:
        #         if '/fov_wells' not in fid:
        #             QMessageBox.critical(self, '',
        #                                  "The FOV was not split",
        #                                  QMessageBox.Ok)
        #             return
        # except (IOError, tables.exceptions.HDF5ExtError):
        #     self.fid = None
        #     self.image_group = None
        #     QMessageBox.critical(
        #         self, '',
        #         "The selected file is not a valid .hdf5. Please select a valid file",
        #         QMessageBox.Ok)
        #     return

        fovsplitter = FOVMultiWellsSplitter(self.vfilename)
        with tables.File(vfilename) as fid:
            img_stack = fid.get_node('/full_data').read().copy()
        tiles_list = fovsplitter.tile_FOV(img_stack)

        self.wells_df = fovsplitter.wells.copy().set_index('well_name')
        self.tiles = {k: v for (k, v) in tiles_list}
        self.well_names = self.wells_df.index.to_list()
        self.ui.wells_comboBox.clear()
        for wi, wn in enumerate(self.well_names):
            self.ui.wells_comboBox.addItem(wn)
        self.updateImGroup(0)

    def updateImGroup(self, well_index):
        if well_index < 0:
            # this happens when clearing the combobox
            return

        self.well_name = self.ui.wells_comboBox.itemText(well_index)
        self.ui.label_well.setText(f'well name: {self.well_name}')
        self.ui.label_well_counter.setText(
            (f'{self.well_names.index(self.well_name)+1}/'
             + f'{len(self.well_names)}'))

        self.image_group = self.tiles[self.well_name].copy()

        self.tot_frames = self.image_group.shape[0]
        self.image_height = self.image_group.shape[1]
        self.image_width = self.image_group.shape[2]

        self.ui.spinBox_frame.setMaximum(self.tot_frames - 1)
        self.ui.imageSlider.setMaximum(self.tot_frames - 1)

        self.frame_number = 0
        self.ui.spinBox_frame.setValue(self.frame_number)

        self.updateImage()
        # self.readCurrentFrame()
        # print(self.frame_img.shape)
        # print(dir(self.frame_img))
        self.mainImage.zoomFitInView()

        return

    def next_well_fun(self):
        self.ui.wells_comboBox.setCurrentIndex(
            min(self.ui.wells_comboBox.currentIndex() + 1,
                self.ui.wells_comboBox.count()-1))

        return

    def prev_well_fun(self):
        self.ui.wells_comboBox.setCurrentIndex(
            max(0, self.ui.wells_comboBox.currentIndex() - 1))
        return


if __name__ == '__main__':
    app = QApplication(sys.argv)

    ui = WellsVideoPlayerGUI()
    ui.show()

    sys.exit(app.exec_())
