# WellAnnotator

Simple GUI for annotating wells.

Point the GUI to a `MaskedVideos` folder (or to a subfolder of `MaskedVideos`, even a few levels down), and it will allow you to annotate all the masked videos in the folder without having to manually loop through the files.


## Installation

Installation steps:
* git clone, or download, this repository in a folder of your computer
* open a terminal window in that folder
* create the virtual environnment from the `environment.yml` file
* activate the newly created virtual environment
* install the code in the directory

In a terminal:
```bash
cd ~/behavgenom_repos
git clone https://github.com/Tierpsy/WellAnnotator.git
conda env create -f environment.yml
conda activate wellannotator
pip install -e .
```

### Updating an existing installation

Assuming that this code was cloned or donwloaded to `~/behavgenom_repos/WellAnnotator` and that the `wellannotator` environment is active, you can update the code by executing
```bash
cd ~/behavgenom_repos/WellAnnotator
git pull
conda env create -f environment.yml
conda activate wellannotator
pip install -e .
```
## Starting the program

Now that the GUI is installed, you can launch it by executing
`well_annotator` in your terminal window (provided the `wellannotator`
environment is active)

You also have acess to two command-line tools:
* `rebase_annotations` to use if you have moved your files to a different drive or folder, and so the path to the annotated files has changed. Type `rebase_annotations --help` for information on how to use the tool correctly.
* `read_working_dir` this allows you to read the common path to the annotated videos, and is the part that gets modified with `rebase_annotations`. Type `read_working_dir --help` for information on how to use the tool correctly.


## How to use

* open the GUI
* drag and drop the folder you want to work in
    * if you've already worked on this folder before, the GUI will have created a `*_wells_annotations.hdf5` file, you can also drag and drop that file
* the GUI will present you with the `full_data` video of each of the wells of the first video
* scroll through the video with the scroll bar below the video, or with the scrollwheel of your mouse
    * don't place the cursor on the video while scrolling, as there is a bug at the moment that will also make the view zoom
* annotate a well by clicking the appropriate button
* move to the next/previous well with the `Next Well`/`Previous Well` buttons
    * note that the well progression indicator will change
* when you've annotated all the wells in a file, use the `Next Video`/`Previous Video` button
    * this will take a couple of seconds, more if you're working on remote data
* save the progress on disk by clicking on the `Save` button
    * you will be prompted to save as you close the GUI. But it's safer to save often!

## How to use the neural network to automatically annotate wells

Note: this only works for 96-well plates with square wells.

* open the GUI
* drag and drop the folder you want to work in
    * if you've already worked on this folder before, the GUI will have created a `*_wells_annotations.hdf5` file, you can also drag and drop that file
* click on the `Run CNN Classifier` button
  * the CNN will overwrite any existing annotation (if you ok the warning), or only classify the unannotated wells if you choose this option in the second warning window
    * progress will be saved to disk every time a new video is loaded
  * wells classified as `good` will be annotated as such
  * wells the classifier thinks are `bad` will be left "unannotated"
  * progress will be shown with a progress bar in the terminal you launched the GUI from
  * use the `Next Well to Review` button to cycle through the wells that the CNN thought were `bad`, and classify them manually as above. The manual step is necessay because the models was tuned to catch as many `bad` wells as possible, but that means that many `good` wells are also classified as `bad`.
* save to disk

### Keyboard Shortcuts

| key | label |
| -:|:-----|
| 1 | good |
| 2 | misaligned |
| 3 | precipitation |
| 4 | contamination |
| 5 | wet |
| 6 | bad agar |
| 7 | other bad |
| 8 | bad lawn |
| 9 | bad worms |
| - (or _ ) | previous well |
| + (or = ) | next well |
| ] (or } ) | next unannotated well |
| < (or , ) | previous video |
| > (or . ) | next video |
| s | save |
| o | open a wells_annotations file |

<img src="https://user-images.githubusercontent.com/33106690/87806850-6161ea80-c84f-11ea-96d0-b063d46664b2.gif" width="800">



## Future improvements
* at the moment the gui ignores any `is_bad_well` info from `/fov_wells` in the masked videos. Will fix this
* create tool to apply the annotations back in the masked videos
* update screen recording
