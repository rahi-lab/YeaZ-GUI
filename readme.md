# YeaZ

This is the user manual for the graphical interface for yeast segmentation using a state of the art convolutional neural network with U-Net architecture. As for now, the convolutional neural network is trained for phase contrast images. Compatability with brightfield images will come soon. You can find the training set with the annotated images here: https://www.epfl.ch/labs/lpbs/data-and-software/. 

## Installation

1. Clone this repository.

2. Download the weights of the neural network under the following link: https://drive.google.com/file/d/1UTivmx_aEMpeGdOkCZO1CS9mcdJ3zmw2/edit. Put it in the folder `/unet`.

3. Make sure that you have python 3, as well as all packages listed in the packages.txt folder, installed. Note that Tensorflow v2 is supported, but as the program was developed with Tensorflow v1.9.0, we cannot promise that it will run bug free. Also, it is imperative to install openpyxl 3.0.1, as a bug in openpyxl 3.0.2 prevents saving to an excel file.

4. Run the program from your command line with `python GUI_main.py`

   

    

