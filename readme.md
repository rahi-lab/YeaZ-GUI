# YeaZ

This is the user manual for the graphical interface for segmenting yeast images using the YeaZ convolutional neural network. You can find the training set with the segmented training images here: https://www.quantsysbio.com/data-and-software/. 

Want to try out the neural network without installing any software? Check out our online segmentation tool at https://lpbs-nn.epfl.ch/.

## Latest updates
25.01.2023:
1. Add GCN Tracker
2. Update installation procedure
3. Fix bugs

## Installation

### System requirements

The software requires a standard computer with enough RAM to apply the neural network. 8 GB RAM is enough to predict the 700 x 500 px image provided as the test data. The RAM requirements scale linearly with the number of image pixels.

It was tested on macOS Ventura (13.4.1), Windows 10 Education, and Ubuntu 20.04.4.

Package dependencies: The convolutional neural network relies on Pytorch. The Hungarian algorithm is implemented in the munkres package. In addition, standard image processing and scientific computing libraries are used. 

Installation time is less than 5 minutes. 
   
### Install from source

follow the instructions below to install the package from source. This is the recommended way of installing the package.

1. If you don't have conda or miniconda installed, download it from https://docs.conda.io/en/latest/miniconda.html.
2. Clone this repository (`git clone https://github.com/rahi-lab/YeaZ-GUI`).
3. In the command line, navigate to the folder where you cloned YeaZ-GUI (command `cd YeaZ-GUI`).
4. Enter the command `source install.sh` (in unix-base systems) or `install.bat` in windows systems. This will create a conda environment named YeaZ and install all the required packages including the YeaZ-toolbox package that stores the primary tools for tracking and analysis. 

    4.1 If you get the 'permission denied' error, try running `chmod +x install.sh` and then run `source install.sh` again.

    4.2 If this didn't work, try running commands in install.sh file one by one.


5. Download weight files for neural network and put them in the yeaz/nns/weights folder.

    5.1. Download the parameters for segmenting phase contrast images from: https://drive.google.com/file/d/1tcdl34Aq11mrPVlyu0Qd4rUigw_6948b.
    
    5.2. Download the parameters for segmenting bright-field images from: https://drive.google.com/file/d/1vnhkp54McM836yczh4F-YYJwPahbTsY0
    
    5.3. Download the parameters for segmenting fission images form: https://drive.google.com/file/d/1h_Wz2d3UY0jkGtMrhl32iEqbOQVXsmKS.


## Runnig the GUI

1. Open a terminal and activate the environment using `conda activate YeaZ`.
2. Run the program with the command `yeaz`.

## Troubleshooting / FAQ 

### Memory error when running on GPU (cuda). Also might happen on CPU.

Unlike CPU, GPU memory is very limited. If you get a memory error when running on GPU, try the following steps:
1. Crop the images to smaller sizes. Memory usage depends on number of pixels in your images. You may try cropping your images into several smaller images or removing empty space around cells.
2. Another application might be using the GPU memory. Try to close all other applications and run the program again. You can also check applications that use GPU memory using the task manager (windows) or `nvidia-smi` command (linux).
3. Try running on CPU or on a cluster with more GPU memory.

### The application is running on CPU instead of GPU

if you have specified running on GPU and the application is running on CPU instead, this might be due to the following reasons:
1. you don't have a cuda compatible gpu. check the list of cuda-compatible gpus here: https://developer.nvidia.com/cuda-gpus
2. you are using mac os with m1 or m2 processors. Unfortunately, the current version of PyTorch implementation does not fully support Mac M1 or M2 GPUs. In the meantime, you can still run your program on Mac M1 or M2 CPUs, which are quite powerful and can provide significant performance gains over traditional CPUs.
3. you have not installed cuda. please follow the installation steps above to install cuda (run `conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia`).

### Small buds are not recognized as cells

If small buds aren't recognized as cells in your image, this is likely linked to a segmentation parameter that is too high. Relaunching the CNN with a smaller parameter will likely yield better results.

### I just want the CNN, but not the GUI

In case you only want to use the functionalities of the convolutional neural network and the segmentation, but not the full GUI, you only need the files `nns/model_pytorch.py`, `nns/neural_network.py` (for making predictions), `nns/segment.py` (for doing watershed segmentation) and `nns/hungarian.py` (for tracking), as well as the weights for the neural network which have to be in the same folder. You can create predictions using the `prediction` function in `neural_network.py` (note that before making predictions, you have to use the function `equalize_adapthist` from `skimage.exposure` on the image). The segmentations can be obtained with the `segment` function in `segment.py`, and tracking between two frames is done using the `correspondence` function in `hungarian.py`.
You can also run `Launch_NN_comand_Line.py` and give input arguments to run the whole pipeline and save final mask. Here is an example for running the CNN on a phase contrast image:
`python Launch_NN_command_line.py -i "example_data/2020_3_19_frame_100_cropped.tif" -m "newmaskfile.h5" --image_type  "pc" --device "cuda" --range_of_frames 0 0 --`

### CNN performs less well on bright-field images

Our CNN was trained on fewer cells with the bright-field technique (3841 unique cells imaged with 6 different exposure levels versus >8000 for phase contrast).

### Graphical user interface not working on Mac OS Big Sur

Jordan Xiao of Stanford University pointed out that one of the python modules (Pyqt) has some issues on Mac OS Big Sur. Check out https://stackoverflow.com/questions/64833558/apps-not-popping-up-on-macos-big-sur-11-0-1 and https://stackoverflow.com/questions/64818879/is-there-any-solution-regarding-to-pyqt-library-doesnt-work-in-mac-os-big-sur/64856281 for more information and possible fixes.

## User Guide

### Launching the Program

Upon starting the program, it prompts you to select your images and your (new) mask file. There are two ways to select images: One can directly select a single image file using the button `Open image file`. Currently, we support Nikon `.nd2` files and multi-stack `.tif` files in addition to all standard formats such as `.png`, `.jpg`, or `.tif`. One can also select a folder of image files using the button `Open image folder`. This takes every single image in the folder to be a frame in a timelapse recording of yeast cells. The folder must contain images that all have the same size. 

The program will save segmentation masks in `.h5` files. You can either create a new file by specifying its name in the text box or if you already have an h5 file for a specific set of images, you can select it using `Open mask file`. Note that when using an existing `.h5` file, you also have to use the same images as you did at its creation.

Depending on the size of your images, it might take up to one minute to load images.

### The Interface

After clicking OK in the launcher, the main program will open. It consists of an image display of three images, the current image in the middle, the previous one to the left and the next image to the right. This display was chosen to easily be able to check whether the cell numbers and the segmentations are consistent throughout time.

On the very bottom of the program, there is a status bar that displays the state of the program. In addition, when hovering over a button, it gives detailed information about what the button does and how to use it.

On the top left of the three images, there are multiple buttons that allow the user to use the pan and zoom to navigate through the image. The home button to the very left allows you to reset zoom and pan, while the arrows allow you to go to the next and previous pan/zoom positions. 

On the bottom of the images, there are three rows of buttons. The first row of buttons allows the user to select the field of view, color channel, and time frame. Note that support for multiple fields of view and color channels is currently only available when opening .nd2 files. The second row contains tools to make edits to the mask, in order to correct the mistakes of the CNN. Moreover, it allows to show or hide the segmentation mask and the cell numbers. On the bottom right, the buttons allow to launch the CNN, to recalculate the tracking, and to extract the fluorescence or segmentation masks.

### Launching the CNN

After opening a new image file, the next step is typically to launch the convolutional neural network with the `Launch CNN` button. Note that if you are using a file with multiple color channels, this has to be done with the brightfield channel visible. This will open a dialog box, in which you can specify the time frames that you want to launch the CNN on as well as the field of view you want to use and type of your images. 

Moreover, it lets you specify two parameters: The **threshold value** specifies the predicted value above which a pixel is considered to belong to a cell. This value is set at 0.5 per default and doesn't have to be changed in our experience. Increasing this value will decrease the sizes of the cells and can come in handy if the cells tend to exceed their borders. The **segmentation parameter** tells the program how far away two cell centers have to be at least, in order for two cells to be considered as separate entities. It has to be adjusted depending on how large the image resolution is: For small resolutions, a value of 2 seems to work well, whereas 5 is good for higher resolutions.

For running CNN, you can specify if the algorithm run on GPU or CPU. While running in GPU is faster, for larger images you might get memory error on GPU. If you get this type of errors, try running on CPU.

Running CNN can take up to hours depending on the number of frames and size of images. For the example data it shouldn't take more than few minutes on a normal computer.

### Making edits to the mask

After the CNN has run, it is possible to correct the mistakes it has made. This can be done in the following ways:

`Add region`: Add a region to an existing cell, by defining a polygon. First left-click on the cell to which you want to add a region, then continue clicking to draw a polygon to add. Finally click on the button again to confirm.

`New cell`: This works similar to `Add region` but defines a new cell. Draw a polygon using left-clicks and re-click the button to confirm.

`Brush`: This is an alternative way to add to a cell. The user right-clicks to select the cell to draw. Then the user can click and drag to draw the cell. The brush size can be controlled using the spin-box to the right.

`Eraser`: This can be used to remove a region from a cell. The use is the same as for `Brush`.

`Exchange cell IDs`: This allows correction of cell ID values by switching two cells. 

`Change cell ID`: This allows changing the ID number of a cell. **Important: **If you change the number to the number of another cell, those two cells will from now on be considered as one single cell. This is useful for fusing cells that were oversegmented but has to be used with care.

`Retrack`: Having made edits to a frame, the cell numbers may no longer correspond in the next frame. This can be automatically fixed by navigating to the next frame and clicking the retrack button.

### Extracting the results

After the masks are satisfactory for a given field of view, you can click on the `Extract` button to export the results. There are two ways the results can be exported: Firstly, the masks that were found can be exported as multistack TIFF files. Secondly, the fluorescence together with several statistics giving information about every individual cell can be extracted and saved as a `.csv` file. 

Moreover, you may only be interested in a subset of the cells visible in the image, which is why this second window allows you to select the cells which you are interested in. You can select or deselect multiple cells by drawing a polygon around them and confirming with a right-click, or select and deselect single cells by just left-clicking them. Note that the image that is displayed corresponds to the last frame for which you have a mask. Cells which disappeared throughout the timelapse video - and thus are not part of the mask - will be exported as well but indicated with a flag in the exported fluorescence csv. 

When you want to extract fluorescence, you can add files from which to extract fluorescence by clicking the `Add` button. There you can either add a single image file, a multistack TIFF file, or a folder containing image files. Note that if multiple files or frames are used, the fluorescence file or folder must have the same amount of images as the image given to the program at startup.

The output csv contains one line for every combination of cells, timeframe, and channel. This allows the file easily to be read into pandas, and avoids a varying amount of columns depending on how many fluorescence channels are used. The following statistics are exported: The *area* of the cell, the *mean* intensity, the intensity *variance*, the *total intensity*, and the x and y coordinates of the *center of mass*. Moreover, the major and minor axes of the cells are found using principal component analysis. In particular, the *angle* of the major axis to the x axis is given, together with the *length* of the major and minor axis, thus, fully specifying an ellipsoid approximating the cell. Finally, we report whether the cell disappears, i.e., whether or not it is present in the last frame. 

### Running the demo

We guide you step-by-step through the demo:

1. In the startup dialog, click `Open image file` and select the file in the `example_data` folder from within the file dialog.
2. Give a name to the h5 mask file, such as example_data.h5. Press `OK` to confirm.
3. We want to predict the segmentation. Click `Launch CNN`. In the pop-up dialog. Enter 0 and 0 as the time bounds. Select the Field of View 1 by clicking on it. Press `OK`. 
4. Wait for the neural network to predict. This takes about 1 min on a standard computer. 
5. Now go through the image to verify the predictions and correct mistakes as needed. Instructions about how to use every tool is shown in the status bar at the bottom when you hover over the tool button. 
6. Click `Extract` if you are satisfied. Extract the mask or the cell statistics, specify a file name, and you're done! In case you wanted additional fluorescence channels or only extract a subset of cells, you could also do this here using the corresponding buttons.





`

