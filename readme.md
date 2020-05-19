# YeaZ

This is the user manual for the graphical interface for yeast segmentation using a state of the art convolutional neural network with U-Net architecture. As for now, the convolutional neural network is trained for phase contrast images. Compatability with brightfield images will come soon. You can find the training set with the annotated images here: https://www.epfl.ch/labs/lpbs/data-and-software/. 

Want to try out the neural network first? Check out our online segmentation tool at https://lpbs-nn.epfl.ch/.

## Installation

1. Clone this repository.
2. Download the weights of the neural network under the following link: https://drive.google.com/file/d/1UTivmx_aEMpeGdOkCZO1CS9mcdJ3zmw2/edit. Put it in the folder `/unet`.
3. Make sure that you have python 3, as well as all packages listed in the packages.txt folder, installed. Note that Tensorflow v2 is supported, but as the program was developed with Tensorflow v1.9.0, we cannot promise that it will run bug free. Also, it is imperative to install openpyxl 3.0.1, as a bug in openpyxl 3.0.2 prevents saving to an excel file.
4. Run the program from your command line with `python GUI_main.py`

## Troubleshooting / FAQ

### Running CNN makes program crash

Using the neural network to make predictions is very memory intensive. This can lead the computer to run out of memory, which in turn causes the program to abort. However, the amount of memory that is needed depends on the size of the image. So cropping the images into several smaller images, removing space without cells around the colonies, or lowering the image resolutoin will allow you to run the program even without access to a super-computer. For instance, using a 2015 MacBook Pro with 8GB of RAM and a 2.9GHz Intel Core i5 CPU, we were able to predict images of size 700 x 500 pixels.

### Small buds aren't recognized as cells

If small buds aren't recognized as cells in your image, this is likely linked to a segmentation parameter that is too high. Relaunching the CNN with a smaller parameter is will likely yield better results.

### I just want the CNN, but not the GUI

In case you only want to use the functionalities of the convolutional neural network and the segmentation, but not the full GUI, you only need the files `unet/model.py`, `unet/neural_network.py` (for making predictions), `unet/segment.py` (for doing watershed segmentation) and `unet/hungarian.py` (for tracking), as well as the weights for the neural network which have to be in the same folder. You can create predictions using the `prediction` function in `neural_network.py`, obtain the segmentations with the `segment` function in `segment.py`, and do tracking between two frames using the `correspondance` function in `hungarian.py`. 

### CNN does badly on bright-field images

Our CNN was trained using only phase contrast images. However, we found that the predictions also perform reasonably well on brightfield images. For this to work, you need to considerably increase the threshold value - a value of 0.95 seems to work well on our examples. We are currently working on training a CNN with brightfield images in order to get even better predictions. 

## User Guide

### Launching the Program

Upon running the program, it promps you to select your images and your save file. There are two ways to select images: On one hand one can directly select a single image file using the button `Open image file`. Currently, we support Nikon `.nd2` files and multi-stack `.tif` files in addition to all standard formats such as `.png`, `.jpg` or `.tif`. On the other hand, one can select a folder of image files using the button `Open image folder`. This considers every single image in the folder to be a frame in a movie of yeast cells. To this effect, the folder has to contain only image files that all have the same size. 

Moreover, while running the program, the segmentation masks will be saved in a `.h5` file. You can either create a new file by specifying its name in the text box, or if you already have an h5 file for a specific set of images, you can select it using `Open mask file`. Note that when using an existing `.h5` file, you also have to use the same images as you did at its creation.

### The Interface

After clicking OK in the launcher, the main program will open. It consists of an image display of three images, the current image in the middle, the previous one to the left and the next image to the right. This display was chosen to easily be able to check whether the cell numbers and the segmentations are consistent throughout time. 

On the very bottom of the program, there is a status bar which displays the state of the program. In addition, when hovering over a button, it gives detailed information about what the button does and how to use it.

On the top left of the three images, there are multiple buttons that allow the user to use pan and zoom to navigate through the image. The home button to the very left allows to reset zoom and pan, while the arrows allow to go to the next and previous pan/zoom positions. 

On the bottom of the images, there are three rows with buttons. The first row of buttons allows the user to select the field of view, color channel and time frame. Note that support for multiple fields of view and color channels is currently only available when opening .nd2 files. The second row contains tools to make edits to the mask, in order to correct mistakes of the CNN. Moreover, it allows to show or hide the segmentation mask and the cell numbers. On the bottom right, the buttons allow to launch the CNN, to recalculate the tracking, and to extract the fluorescence or segmentation masks.

### Launching the CNN

After you've opened a new image file, the next step is typically to launch the convolutional neural network with the `Launch CNN` button. Note that if you are using a file with multiple color channels, this has to be done with the brightfield channel visible. This will open a dialog box, in which you can specify the time frames that you want to launch the CNN on as well as the field of view you want to use. 

Moreover, it lets you specify two parameters: The **threshold value** specifies the predicted value above which a pixel is considered to belong to a cell. This value is set at 0.5 per default and doesn't have to be changed in our experience. Augmenting it will make less pixels be considered as cells and can come in handy if the cells tend to exceed their borders. The **segmentation parameter** tells the program how far away two cell centers have to be at least, in order for two cells to be considered as separate entities. It has to be adjusted depending on how large the image resolution is: For small resolutions, a value of 3 seems to work well, whereas 10 is good for larger resolutions.

###Making edits to the mask

After the CNN has run, it is possible to correct the mistakes it has made. This can be done in the following way:

`Add region`: Add a region to an existing cell, by defining a polygon. First left-click on the cell to which you want to add a region, then continue clicking to draw a polygon to add. Finally click on the button again to confirm.

`New cell`: This works similarly as `Add region`, but defines a new cell. Draw a polygon using left-clicks and re-click the button to confirm.

`Brush`: This is an alternative way to add to a cell. The user right-clicks to select the cell to draw. Then he can click and drag to draw the cell. The brush size can be controlled using the spin-box to the right.

`Eraser`: This can be used to remove a region from a cell. The use is the same as for `Brush`.

`Exchange Cell Values`: This allows to correct the cell values by switching two cells. 

`Change Cell Value`: This allows to change the value of a cell. **Important: **If you change the number to the number of another cell, those two cells will from now on be considered as one single cell. This is useful for fusing cells that were oversegmented, but has to be used with care.



`