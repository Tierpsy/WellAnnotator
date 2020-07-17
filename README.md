# WellAnnotator

Simple GUI for annotating wells.

Point the GUI to a `MaskedVideos` folder (or to a subfolder of `MaskedVideos`, even a few levels down), and it will allow you to annotate all the masked videos in the folder without having to manually loop through the files.


## Installation

* git clone, or download, this repository in a folder of your computer
* activate the conda environment for Tierpsy
* execute the `well_annotator/WellAnnotator.py` program

Better installation instructions, and friendlier launcher, will follow soon.


## How to use

* open the GUI
* drag and drop the folder you want to work in
    * if you've already worked on this folder before, the GUI will have created a `*_wells_annotations.hdf5` file, you can also drag and drop that file
* the GUI will present you with the `full_data` video of each of the wells of the first video
* scroll through the video with the scroll bar below the video, or with the scrollwheel of your mouse
    * don't place the cursor on the video while scrolling, as there is a bug at the moment that will also make the view zoom
* annotate a well by either clicking the appropriate button, or use numbers on your keyboard:

| key | label |
| -:|:-----|
| 1 | good |
| 2 | misaligned |
| 3 | precipitation |
| 4 | contamination |
| 5 | wet |
| 6 | bad agar |
| 7 | other bad |

* move to the next/previous well with the `Next Well`/`Previous Well` buttons, or with the dropdown menu
    * note that the well progression indicator will change
* when you've annotated all the wells in a file, use the `Next Video`/`Previous Video` button to move to the next video
    * this will take a couple of seconds, more if you're working on remote data
* save the progress on disk by clicking on the `Save` button
    * you will be prompted to save as you close the GUI. But it's safer to save often

<img src="https://user-images.githubusercontent.com/33106690/87806850-6161ea80-c84f-11ea-96d0-b063d46664b2.gif" width="800">



## Future improvements
* more keyboard shortcut
* disable scrollwheel-based zooming (when mouse focus on video area)
* better installation instructions
* create an entry point for easier launching
* at the moment the gui ignores any `is_bad_well` info from `/fov_wells` in the masked videos. Will fix this
* create tool to apply the annotations back in the masked videos
* better screen recording
