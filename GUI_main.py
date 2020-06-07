#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script is the main script used to produce a GUI which should help for
cell segmentation. This script can only read .nd2 files containing the 
images of cells, especially it displays for each recorded positions (field
of view) the pictures in the time axis.

The script opens first a window which allows you to load an nd2 file and
to load or create an hdf file. The hdf file contains all the masks, so if
it is the first the user segments an nd2 file, a new one should be created.
And it can be then loaded for later use.  Along with new hdf file, created
by the name entered by the user (say filename), it creates three other hdf 
files (filename_predicted.h5, filename_thresholded.h5 and 
filename_segmented.h5) these contain all the steps of the NN to get to the 
segmented picture. 

After the first window is finished a second one opens, where at each time 
index, three pictures 
are displayed the t-1 picture, the t picture (current frame which can be
edited) and the t+1 picture. Using the arrows one can navigate through time.
On top of the picture, there is always a mask which is displayed, if no cells
are present in the mask then the mask is blank and the user does not see it. 
If one wants to hand anmotate the pictures, one can just start to draw on the
picture using the different functions (New Cell, Add Region, Brush, Eraser,
Save Mask, ...) and the informations will be saved in the mask overlayed on 
top of the pictures. 

If one wants to segment using a neural network, one can press the
corresponding button (Launch CNN) and select the time range and 
the field of views on which the neural network is applied.

Once the neural network has finished predicting, there are still no visible
masks, but on the field of views and time indices where the NN has been
applied, the threshold and segment buttons are enabled. By checking these
two buttons one can either display the thresholded image of the prediction or
display the segmentation of the thresholded prediction.

At this stage, one can correct the segmentation of the prediction using
the functions (New Cell, Add Region, etc..) by selecting the Segment
checkbox and then save them using the Save Seg button.
If the user is happy with the segmentation, the Cell Correspondence button 
can be clicked. Until then, the cells get random numbers attributed by
the segmentation algorithm. In order to keep track of the cell through time,
the same cells should have the same number between two different time pictures.
This can be (with some errors) achieved by the Cell Correspondence button,
which tries to attribute the same number to corresponding cells in time.
After that, the final mask is saved and it is always visible when you go on
the corresponding picture. This mask can also be corrected using the 
usual buttons (because the Cell Correspondence makes also mistakes). 

"""
import sys
import numpy as np
import pandas as pd
import h5py
import skimage

# For writing excel files
#from openpyxl import load_workbook
#from openpyxl import Workbook

# Import everything for the Graphical User Interface from the PyQt5 library.
from PyQt5.QtWidgets import (QApplication, QMainWindow, QDialog, QSpinBox,
    QMessageBox, QPushButton, QCheckBox, QAction, QStatusBar, QLabel)
from PyQt5 import QtGui

#Import from matplotlib to use it to display the pictures and masks.
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from sklearn.decomposition import PCA
import imageio

#append all the paths where the modules are stored. Such that this script
#looks into all of these folders when importing modules.
sys.path.append("./unet")
sys.path.append("./disk")
sys.path.append("./icons")
sys.path.append("./init")
sys.path.append("./misc")

#Import all the other python files
#this file handles the interaction with the disk, so loading/saving images
#and masks and it also runs the neural network.
import Reader as nd

#this file contains a dialog window that takes two integers as entry to swap
#two cell values
import ExchangeCellValues as ecv

#this file contains a dialog window which is opened before the main program
#and allows to load the nd2 and hdf files by browsing through the computer.
import DialogFileBrowser as dfb

#this file contains a window that opens to change the value of one cell. It 
#is opened as soon as the user presses with the left click on a specific cell.
import ChangeOneCellValue as cocv

#this file contains a dialog window where a time range and the field of views
#can be selected to then launch a prediction of the neural network on
#a specific range of pictures.
import LaunchBatchPrediction as lbp

#this file initializes all the buttons present in the gui, sets the shortcuts
#to these buttons and also connect the buttons to the function that are 
#triggered when the buttons are pressed.
import InitButtons

#this file contains the layout of the main window so it justs puts the buttons
#and the pictures at the desired position in the main window.
import InitLayout

# PlotCanvas for fast plotting
from PlotCanvas import PlotCanvas

import Extract as extr
from image_loader import load_image
from segment import segment
import neural_network as nn




class NavigationToolbar(NavigationToolbar):
    """This is the standard matplotlib toolbar but only the buttons
    that are of interest for this gui are loaded. These buttons allow 
    to zoom into the pictures/masks and to navigate in the zoomed picture. 
    A Home button can be used to set the view back to the original view.
    """
    toolitems = [t for t in NavigationToolbar.toolitems if
                 t[0] in ('Home', 'Pan', 'Zoom','Back', 'Forward')]
      
class App(QMainWindow):
    """This class creates the main window.
    """

    def __init__(self, nd2pathstr, hdfpathstr, newhdfstr):
        super().__init__()
        self.setWindowTitle('YeaZ')

        # all these ids are integers which are used to set a connection between
        # the button and the function that this button calls.
        # There are three of them because it happens that one can trigger three 
        # different functions with one button.        
        self.id = 0
        self.id2 = 0
        self.id3 = 0 

        self.reader = nd.Reader(hdfpathstr, newhdfstr, nd2pathstr)
        
        # these variables are used to create/read/load the excel file used
        # to write the fluorescence values extracted. For each field of view,
        # the user will be asked each time to create a new xls file for the 
        # field of view or to load an existing field of view (this is the role
        # of the boolean variable)
        self.xlsfilename = ''
        self.nd2path = nd2pathstr
        
        # Set the indices for the time axis and the field of view index. These
        # indices represent everywhere the current picture (the one that can be
        # edited, i.e. the time t frame)
        self.Tindex = 0
        self.FOVindex = 0
        
        # loading the first images of the cells from the nd2 file
        self.currentframe = self.reader.LoadOneImage(self.Tindex,self.FOVindex)
        
        # check if the t+1 time frame exists, avoid failure if there is only
        # one picture in the folder/nd2 file
        if self.Tindex+1 < self.reader.sizet:
            self.nextframe = self.reader.LoadOneImage(self.Tindex+1, self.FOVindex)
        else:
            self.nextframe = np.zeros([self.reader.sizey, self.reader.sizex])
        
        self.previousframe = np.zeros([self.reader.sizey, self.reader.sizex])

        # loading the first masks from the hdf5 file
        self.mask_curr = self.reader.LoadMask(self.Tindex, self.FOVindex)
        self.mask_previous = np.zeros([self.reader.sizey, self.reader.sizex])
        
        # check if the t+1 mask exists, avoid failure if there is only
        # one mask in the hdf file
        if self.Tindex+1 < self.reader.sizet:
            self.mask_next = self.reader.LoadMask(self.Tindex+1, self.FOVindex)
        else:
            self.mask_next = np.zeros([self.reader.sizey, self.reader.sizex])
        
        # creates a list of all the buttons, which will then be used in order
        # to disable all the other buttons at once when one button/function
        # is pressed/used in the gui.
        self.buttonlist = []
        
        # setting buttons as attributes
        # the shortcuts for the buttons, the functions to which they are
        # connected to,... are all set up in the ButtonInit file which is called
        # in the self.initUI() method below.
        self.button_newcell = QPushButton("New cell")
        self.buttonlist.append(self.button_newcell)
        
        self.button_add_region = QPushButton("Add region")
        self.buttonlist.append(self.button_add_region)
        
        self.button_drawmouse = QPushButton('Brush')
        self.buttonlist.append(self.button_drawmouse)
        
        self.button_eraser = QPushButton('Eraser')
        self.buttonlist.append(self.button_eraser)
        
        self.label_brushsize = QLabel('Brush/Eraser radius:')
        self.spinbox_brushsize = QSpinBox()
        self.buttonlist.append(self.spinbox_brushsize)
        
        self.button_exval = QPushButton('Exchange cell IDs')
        self.buttonlist.append(self.button_exval)
        
        self.button_showval = QCheckBox('Show cell IDs')
        self.buttonlist.append(self.button_showval)
        
        self.button_hidemask = QCheckBox('Hide mask')
        self.buttonlist.append(self.button_hidemask)
        
        self.button_nextframe = QPushButton("Next time frame")
        self.buttonlist.append(self.button_nextframe)
        
        self.button_previousframe = QPushButton("Previous time frame")
        self.buttonlist.append(self.button_previousframe)
        
        self.button_cnn = QPushButton('Launch CNN')
        self.buttonlist.append(self.button_cnn)
        
        self.button_cellcorespondance = QPushButton('Retrack')
        self.buttonlist.append(self.button_cellcorespondance)
        
        self.button_changecellvalue = QPushButton('Change cell ID')
        self.buttonlist.append(self.button_changecellvalue)        
        
        self.button_extractfluorescence = QPushButton('Extract')
        self.buttonlist.append(self.button_extractfluorescence)
        
        self.button_hide_show = QPushButton('CNN')
        self.buttonlist.append(self.button_hide_show)
        
        self.initUI()


    def initUI(self):
        """Initializing the widgets contained in the window. 
        Especially, it creates the widget to plot the 
        pictures/masks by creating an object of the PlotCanvas class self.m. 
        Every interaction with the masks or the pictures (loading new
        frames/editing the frames/masks) occurs through this class.
        
        This method initializes all the buttons with the InitButtons file.
        It connects the buttons to the functions that they should trigger,
        it sets the shortcuts to the buttons, a tool tip, 
        eventually a message on the status bar when the user hovers 
        over the button, etc..
        
        This function also sets all the layout in the InitLayout file. It 
        takes and places the widgets (buttons, canvas, toolbar).

        The function initializes a Menu Bar to have a menu which can be 
        improved later on.
        It sets a toolbar of the matplotlib library and hides it. But it allows
        to connect to the functions of this toolbar through "homemade" 
        QPushButtons instead of the ones provided by matplotlib.
        Finally, it sets a StatusBar which displays some text to describe
        the use of some buttons, or to show that the program is working on 
        something (running the neural network, loading frames, etc...)
        
        After all this has been initialized, the program is ready to be used.
        """
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)

        # Here our canvas is created where using matplotlib, 
        # one can plot data to display the pictures and masks.
        self.m = PlotCanvas(self)
        
        # Initialize all the buttons that are needed and the functions that are 
        # connected when the buttons are triggered.
        InitButtons.Init(self)
        InitLayout.Init(self)
        
        # MENU, TOOLBAR AND STATUS BAR
        # creates a menu just in case, some other functions can be added later
        # in this menu.
#        menubar = self.menuBar()
#        self.fileMenu = menubar.addMenu('File')   
#        self.saveactionmenu = QAction('Save')
#        self.fileMenu.addAction(self.saveactionmenu)
#        self.saveactionmenu.triggered.connect(self.SaveMask)
        
        # hide the toolbar and instead of the original buttons of matplotlib,
        # QPushbuttons are used and are connected to the functions of the toolbar
        # it is than easier to interact with these buttons (for example to 
        # to disable them and so on..)
        self.Nvgtlbar = NavigationToolbar(self.m, self)
        self.addToolBar(self.Nvgtlbar)
        self.Nvgtlbar.hide()
        
        # creates a status bar with user instructions
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBarText = QLabel()
        self.statusBar.addWidget(self.statusBarText)
                
        self.show()
                
        
# -----------------------------------------------------------------------------
# FUNCTIONS LINKED TO NAVIGATION
# connect the functions of the toolbar to our custom QPushbuttons.
    def ZoomTlbar(self):
        """The button_zoom is connected to the zoom function of the toolbar 
        already present in the matplotlib library.
        
        Depending on the buttons that are active or checked, when the zoom 
        function is used, it does not disable all the buttons.
        
        If the segment and threshold button are not checked or used
        when the zoom button is clicked, it disables all the button
        using self.Disable which disables everything except the button passed
        in argument (in this case button_zoom).
        
        If the zoom button is used while the segment button is checked,
        it disables all the buttons (1st elif) except the segment button
        but once it is finished (so the zoom button becomes unchecked) 
        then it enables only the editing buttons (as long as the segment
        button is still checked) such as New Cell, Add Region, Eraser, 
        Brush,etc.. and the other toolbar buttons (3rd elif)
        
        
        If the zoom button is clicked while the threshold button is checked,
        it disables all the button except the threshold button (2nd elif).
        Once the zoom button is unchecked, it enables the toolbar buttons
        (4th elif)
        In any other case, it just enables all the buttons again.
        """
        self.Nvgtlbar.zoom()
        
        if (self.button_zoom.isChecked()):
            self.Disable(self.button_zoom)
            
        else:
            self.Enable(self.button_zoom)
        
        
    def HomeTlbar(self):
        """
        connects the home button to the home function of the matplotlib
        toolbar. It sets the view to the original view (no zoom)
        """
        self.Nvgtlbar.home()

            
    def BackTlbar(self):
        """
        It calls the back function of the matplotlib toolbar which sets the 
        view to the previous one (if the user does several zooms/pans, 
        this button allows to go back in the "history of views")
        """
        self.Nvgtlbar.back()

        
    def ForwardTlbar(self):
        """
        It calls the forward function of the matplotlib toolbar which sets the 
        view to the next one (if the user does several zooms/pans, 
        this button allows to go forward in the "history of views"
        """
        self.Nvgtlbar.forward()

    
    def PanTlbar(self):
        """The button_pan is connected to the pan function of the toolbar 
        already present in the matplotlib library.
        
        Depending on the buttons that are active or checked, when the pan 
        function is used, it does not disable all the buttons.
        
        If the segment and threshold button are not checked or used
        when the pan button is clicked, it disables all the button
        using self.Disable which disables everything except the button passed
        in argument (in this case button_pan).
        
        If the pan button is used while the segment button is checked,
        it disables all the buttons (1st elif) except the segment button
        but once it is finished (so the zoom button becomes unchecked) 
        then it enables only the editing buttons (as long as the segment
        button is still checked) such as New Cell, Add Region, Eraser, 
        Brush,etc.. and the other toolbar buttons (3rd elif)
        
        
        If the pan button is clicked while the threshold button is checked,
        it disables all the button except the threshold button (2nd elif).
        Once the pan button is unchecked, it enables the toolbar buttons
        (4th elif)
        In any other case, it just enables all the buttons again.
        """

        self.Nvgtlbar.pan()

        if (self.button_pan.isChecked()):
            self.Disable(self.button_pan)
        else:
            self.Enable(self.button_pan)

            
    def ButtonFluo(self):
        """This function is called everytime the Extract Fluorescence button is 
        clicked (self.button_extractfluorescence). 
        """        
        self.Disable(self.button_extractfluorescence)
        self.WriteStatusBar('Extracting ...')
        
        # Get last image with mask
        for time_index in range(self.reader.sizet-1, -1, -1):            
            # Test if time has a mask
            file = h5py.File(self.reader.hdfpath, 'r+')
            time_exist = self.reader.TestTimeExist(time_index, self.FOVindex, file)
            file.close()
            
            if not time_exist:
                continue
            
            # load picture and sheet
            image = self.reader.LoadImageChannel(time_index, self.FOVindex, 
                                                 self.reader.default_channel)
            mask = self.reader.LoadMask(time_index, self.FOVindex)
            
            # Break if mask is non-empty
            if mask.sum()>0:
                break
            
            if time_index==0:
                QMessageBox(self, 'Error', 'No mask found')
                self.Enable(self.button_extractfluorescence)
                self.ClearStatusBar()
        
        # Launch dialog with last image
        dlg = extr.Extract(image, mask, self.reader.channel_names)
        dlg.exec()
        if dlg.exit_code == 1: # Fluorescence
            self.ExtractFluo(dlg.cells, dlg.desel_cells, dlg.outfile, dlg.file_list)
        elif dlg.exit_code == 2: # Mask
            self.ExtractMask(dlg.desel_cells, dlg.outfile)
            
        self.Enable(self.button_extractfluorescence)
        self.ClearStatusBar()


    def ExtractMask(self, desel_cells, outfile):
        """Extract the mask to the specified tiff file. Only take cells 
        specified by the cell_list"""
        
        mask_list = []
        for time_index in range(0, self.reader.sizet):
            
            # Test if time has a mask
            file = h5py.File(self.reader.hdfpath, 'r+')
            time_exist = self.reader.TestTimeExist(time_index, self.FOVindex, file)
            file.close()
            
            if not time_exist:
                continue
            
            mask = self.reader.LoadMask(time_index, self.FOVindex)
            for cell in desel_cells:
                mask[mask==cell] = 0
            mask_list.append(mask)
            
        imageio.mimwrite(outfile, np.array(mask_list, dtype=np.uint16))
                        

    def ExtractFluo(self, sel_cells, desel_cells, csv_filename, channel_list):
        """This is the function that takes as argument the filepath to the xls
        file and writes in the file.
        It iterates over the different channels (or the sheets of the file,
        each channel has one sheet.), and reads the image corresponding
        to the time, field of view and channel index. It reads the already
        existing file and makes a copy in which the data will be written in it.
        
        The first step of calculating the data is to iterate through each
        cell/segment of the mask (so each cell is a submatrix of one value
        in the matrix of the mask).
        For each of these value /cell, the area is extracted as being
        the number of pixels corresponding to this cell/value. 
        (it is known from the microscope settings how to convert
        the pixel in area).
        The total intensity is just the value of the pixel and it is added over
        all the pixels corresonding to the cell/value.
        The mean is then calculated as being the total intensity divided by
        the number of pixels (which here is equal to the area also).
        With the mean it is then possible to calculate the variance of the 
        signal for one cell/value.
        
        Then, it is checked if the value of the cell (cell number) already
        exists in the first column, if it already exists it continues to
        find the column corresponding to the time index where the values
        should be written. It sets the flag to True such that it does not
        write the cell as new one and adds it at the end of the column
        
        If the value is not found in the cell number column (new cell or
        first time writing in the file), the flag is False, thus it adds the 
        cell number at the end of the column.
        It then saves the xls file.
        
        """
        # List of cell properties
        cell_list = []

        for time_index in range(0, self.reader.sizet):
            # Test if time has a mask
            file = h5py.File(self.reader.hdfpath, 'r+')
            time_exist = self.reader.TestTimeExist(time_index, self.FOVindex, file)
            file.close()
            
            if not time_exist:
                continue
            
            mask = self.reader.LoadMask(time_index, self.FOVindex)
            
            for channel in channel_list:
                # check if channel is in list of nd2 channels
                try:
                    channel_ix = self.reader.channel_names.index(channel)
                    image = self.reader.LoadImageChannel(time_index, self.FOVindex, channel_ix)
                
                # channel is a file
                except ValueError:
                    image = load_image(channel, ix=time_index)
                    
                for val in np.unique(mask):
                    # bg is not cell
                    if val == 0:
                        continue
                    # disregard cells not in cell_list
                    if (val in desel_cells):
                        continue
                    
                    # Calculate stats
                    stats = {'Cell': val,
                             'Time': time_index,
                             'Channel': channel}
                    
                    stats = {**stats,
                             **self.cell_statistics(image, mask == val)}
                    stats['Disappeared in video'] = not (val in sel_cells)
                    cell_list.append(stats)
                    
        
        # Use Pandas to write csv
        df = pd.DataFrame(cell_list)
        df = df.sort_values(['Cell', 'Time'])
        df.to_csv(csv_filename, index=False)
                    
        self.Enable(self.button_extractfluorescence)
        self.ClearStatusBar()


    def cell_statistics(self, image, mask):
        """Calculate statistics about cells. Passing None to image will
        create dictionary to zeros, which allows to extract dictionary keys"""
        if image is not None:
            cell_vals = image[mask]
            area = mask.sum()
            tot_intensity = cell_vals.sum()
            mean = tot_intensity/area if area > 0 else 0
            var = np.var(cell_vals)
            
            # Center of mass
            y,x = mask.nonzero()
            com_x = np.mean(x)
            com_y = np.mean(y)
            
            # PCA only works for multiple points
            if area > 1:
                pca = PCA().fit(np.array([y,x]).T)
                pc1_x, pc1_y = pca.components_[0,:]
                angle = np.arctan(pc1_y / pc1_x) / np.pi * 360
                v1, v2 = pca.explained_variance_
                
                len_maj = 4*np.sqrt(v1)
                len_min = 4*np.sqrt(v2)
            else:
                angle = 0
                len_maj = 1
                len_min = 1
            
        else:
            mean = 0
            var = np.nan
            tot_intensity = 0
            com_x = np.nan
            com_y = np.nan
            angle = np.nan
            len_maj = np.nan
            len_min = np.nan
        
        return {'Area': area,
                'Mean': mean,
                'Variance': var,
                'Total Intensity': tot_intensity,
                'Center of Mass X': com_x,
                'Center of Mass Y': com_y,
                'Angle of Major Axis': angle,
                'Length Major Axis': len_maj,
                'Length Minor Axis': len_min}

# -----------------------------------------------------------------------------
# NEURAL NETWORK
    def ShowHideCNNbuttons(self):
        """hide and show the buttons corresponding to the neural network.
            this function is called by the button CNN which is hidden. But
            if activated in the InitLayout.py then you can have a button
            which hides the CNN buttons (which are now on the normal also
            hidden...).
        """
        if self.button_hide_show.isChecked():
            self.button_cnn.setVisible(True)

        else:
            self.button_cnn.setVisible(False)
            

    def LaunchBatchPrediction(self):
        """This function is called whenever the button Launch CNN is pressed.
        It allows to run the neural network over a time range and selected
        field of views.
            
        It creates a dialog window with two entries, that define the time range
        and a list where the user can select the desired fields of view.
        
        Once it reads all the value, it calls the neural network function
        inside of self.PredThreshSeg and it does the prediction of the neural
        network, thresholds this prediction and then segments it.
        """
        def reset():
            self.m.UpdatePlots()
            self.ClearStatusBar()
            self.Enable(self.button_cnn)
            self.EnableCNNButtons()
        
        
        self.WriteStatusBar('Running the neural network...')
        self.Disable(self.button_cnn)

        # creates a dialog window from the LaunchBatchPrediction.py file
        dlg = lbp.CustomDialog(self)
        
        # this if tests if the user pressed 'ok' in the dialog window
        if dlg.exec_() == QDialog.Accepted:
            # it tests if the user has entered some values
            # if not it ignores and returns.
            if not (dlg.entry1.text()!= '' and dlg.entry2.text() != ''):
                QMessageBox.critical(self, "Error", "No Time Specified")
                reset()
                return 
            
            # reads out the entry given by the user and converts the index
            # to integers
            time_value1 = int(dlg.entry1.text())
            time_value2 = int(dlg.entry2.text())
    
            # it tests if the first value is smaller or equal such that
            # time_value1 is the lower range of the time range
            # and time_value2 the upper boundary of the range.
            if time_value1 > time_value2 :
                QMessageBox.critical(self, "Error", 'Invalid Time Constraints')
                reset()
                return
            
            # displays that the neural network is running
            self.WriteStatusBar('Running the neural network...')
    
            #it iterates in the list of the user-selected fields 
            #of view, to return the corresponding index, the function
            #dlg.listfov.row(item) is used which gives an integer
            if len(dlg.listfov.selectedItems())==0:
                QMessageBox.critical(self, "Error", "No FOV Selected")
            
            for item in dlg.listfov.selectedItems():
                #iterates over the time indices in the range
                for t in range(time_value1, time_value2+1):                    
                    #calls the neural network for time t and selected
                    #fov
                    if dlg.entry_threshold.text() !=  '':
                        thr_val = float(dlg.entry_threshold.text())
                    else:
                        thr_val = None
                    if dlg.entry_segmentation.text() != '':
                        seg_val = int(dlg.entry_segmentation.text())
                    else:
                        seg_val = 10
                    is_pc = dlg.radiobuttons.checkedId() == 1
                    self.PredThreshSeg(t, dlg.listfov.row(item), thr_val, seg_val,
                                       is_pc)
                    
                    # apply tracker if wanted and if not at first time
                    temp_mask = self.reader.CellCorrespondence(t, dlg.listfov.row(item))
                    self.reader.SaveMask(t,dlg.listfov.row(item), temp_mask)
            
            self.ReloadThreeMasks()
        reset()

    
    def PredThreshSeg(self, timeindex, fovindex, thr_val, seg_val, 
                      is_pc):
        """
        This function is called in the LaunchBatchPrediction function.
        This function calls the neural network function in the
        InteractionDisk.py file and then thresholds the result
        of the prediction, saves this thresholded prediction.
        Then it segments the thresholded prediction and saves the
        segmentation. 
        """
        print('--------- Segmenting field of view:',fovindex,'Time point:',timeindex)
        im = self.reader.LoadOneImage(timeindex, fovindex)
        try:
            pred = self.LaunchPrediction(im, is_pc)
        except ValueError:
            QMessageBox.critical(self, 'Error',
                                 'The neural network weight files could not '
                                 'be found. Make sure to download them from '
                                 'the link in the readme and put them into '
                                 'the folder unet')
            return

        thresh = self.ThresholdPred(thr_val, pred)
        seg = segment(thresh, pred, seg_val)
        self.reader.SaveMask(timeindex, fovindex, seg)
        print('--------- Finished segmenting.')
          
          
    def LaunchPrediction(self, im, is_pc):
        """It launches the neural neutwork on the current image and creates 
        an hdf file with the prediction for the time T and corresponding FOV. 
        """
        im = skimage.exposure.equalize_adapthist(im)
        im = im*1.0;	
        pred = nn.prediction(im, is_pc)                        
        return pred


    def ThresholdPred(self, thvalue, pred):     
        """Thresholds prediction with value"""
        if thvalue == None:
            thresholdedmask = nn.threshold(pred)
        else:
            thresholdedmask = nn.threshold(pred,thvalue)
        return thresholdedmask

    
    def SelectChannel(self, index):
        """This function is called when the button to select different channels
        is used. From the displayed list in the button, the chosen index
        corresponnds to the same index in the list of channels from the reader.
        So, it sets the default channel with the new index (called index below)
        """
        self.reader.default_channel = index
        # update the pictures using the same function as the one used to 
        # change the fields of view.
        self.ChangeFOV()
        

    def SelectFov(self, index):
        """This function is called when the button containing the list of 
        fields od view is used.
        The index correspondds to the field of view selected in the list.
        """
        # mask is automatically saved.
        self.reader.SaveMask(self.Tindex, self.FOVindex, self.m.plotmask)
        self.FOVindex = index    
        
        # it updates the fov in the plot with the new index.
        self.ChangeFOV()
                
        
    def ChangeFOV(self):
        """
        it changes the fov or channel according to the choice of the user
        and it updates the plot shown and it initializes the new fov/channel
        at t=0 by default.
        """
        
        self.Tindex = 0
        
        # load the image and mask for the current plot
        self.m.currpicture = self.reader.LoadOneImage(self.Tindex,self.FOVindex)
        self.m.plotmask = self.reader.LoadMask(self.Tindex,self.FOVindex)
        
        # sets the image and the mask to 0 for the previous plot
        self.m.prevpicture = np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
        self.m.prevplotmask = np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
        
        # load the image and the mask for the next plot, check if it exists
        if self.Tindex+1 < self.reader.sizet:
            self.m.nextpicture = self.reader.LoadOneImage(self.Tindex+1, self.FOVindex)
            self.m.nextplotmask = self.reader.LoadMask(self.Tindex+1, self.FOVindex)
            
            # enables the next frame button in case it was disabled when the 
            # fov/channel was changed
            self.button_nextframe.setEnabled(True)
        else:
            self.m.nextpicture = np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
            self.m.nextplotmask =  np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
            
            # disables the next frame button if the mask or the picture
            # does not exist.
            self.button_nextframe.setEnabled(False)
            
        # once the images and masks are loaded into the variables, they are 
        # displaye in the gui.
        self.m.UpdatePlots()
        
        # disables the previous frame button in case it was active before 
        # changing fov/channel.
        self.button_previousframe.setEnabled(False)
        
        # updates the title of the plots to display the right time indices
        # aboves the plots.
        self.UpdateTitleSubplots()
            
        # if the button to hide the mask was checked before changing fov/channel,
        # it hides the mask again.
        if self.button_hidemask.isChecked():
            self.m.HideMask()
        
        # the button to set the time index is also set to 0/default again.
        self.button_timeindex.setText('')
        # enables the neural network buttons if there is already an 
        # existing prediction for the current image.
        self.EnableCNNButtons()
        
        
    def ReloadThreeMasks(self):
        """
        A function which replots all the masks at the current time and fov 
        indices. Needed after the batch prediction is completed to display
        the result of the NN.
        """
        
        if self.Tindex >= 0 and self.Tindex <= self.reader.sizet-1:
            if self.Tindex == 0:
                self.button_nextframe.setEnabled(True)
                
                if self.Tindex < self.reader.sizet-1:
                    self.m.nextplotmask = self.reader.LoadMask(self.Tindex+1, self.FOVindex)
                else:
                    np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
                
                self.m.plotmask = self.reader.LoadMask(self.Tindex, self.FOVindex)
                self.m.prevplotmask = np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
                self.m.UpdatePlots()
                self.button_previousframe.setEnabled(False)
                
                
            elif self.Tindex == self.reader.sizet-1:
                self.button_previousframe.setEnabled(True)
                self.m.prevplotmask = self.reader.LoadMask(self.Tindex-1, self.FOVindex)
                self.m.plotmask = self.reader.LoadMask(self.Tindex, self.FOVindex)
                self.m.nextplotmask =  np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
                self.m.UpdatePlots()
                self.button_nextframe.setEnabled(False)
                
            else:
                self.button_nextframe.setEnabled(True)
                self.button_previousframe.setEnabled(True)
                self.m.prevplotmask = self.reader.LoadMask(self.Tindex-1, self.FOVindex)
                self.m.plotmask = self.reader.LoadMask(self.Tindex, self.FOVindex)              
                self.m.nextplotmask = self.reader.LoadMask(self.Tindex+1, self.FOVindex)
                self.m.UpdatePlots()
            
            self.UpdateTitleSubplots()
                        
            if self.button_hidemask.isChecked():
                self.m.HideMask()
            self.EnableCNNButtons()
        
        else:
            return
        
    
    def ChangeTimeFrame(self):
        """This funcion is called whenever the user gives a new time index, 
        to jump to the new given index, once "enter" button is pressed.
        """
        
        # it reads out the text in the button and converts it to an int.
        newtimeindex = int(self.button_timeindex.text())
        if newtimeindex >= 0 and newtimeindex <= self.reader.sizet-1:
            self.reader.SaveMask(self.Tindex, self.FOVindex, self.m.plotmask)
            
            self.Tindex = newtimeindex
            
            if self.Tindex == 0:
                self.button_nextframe.setEnabled(True)
                self.m.nextpicture = self.reader.LoadOneImage(self.Tindex+1,self.FOVindex)
                self.m.nextplotmask = self.reader.LoadMask(self.Tindex+1, self.FOVindex)
                
                self.m.currpicture = self.reader.LoadOneImage(self.Tindex, self.FOVindex)
                self.m.plotmask = self.reader.LoadMask(self.Tindex, self.FOVindex)
                
                self.m.prevpicture = np.zeros([self.reader.sizey, self.reader.sizex], 
                                              dtype = np.uint16)
                self.m.prevplotmask = np.zeros([self.reader.sizey, self.reader.sizex], 
                                               dtype = np.uint16)
    
                self.m.UpdatePlots()
                self.button_previousframe.setEnabled(False)
                
            elif self.Tindex == self.reader.sizet-1:
                self.button_previousframe.setEnabled(True)
                self.m.prevpicture = self.reader.LoadOneImage(self.Tindex-1, self.FOVindex)
                self.m.prevplotmask = self.reader.LoadMask(self.Tindex-1, self.FOVindex)
                   
                self.m.currpicture = self.reader.LoadOneImage(self.Tindex, self.FOVindex)
                self.m.plotmask = self.reader.LoadMask(self.Tindex, self.FOVindex)
                  
                self.m.nextpicture =  np.zeros([self.reader.sizey, self.reader.sizex], 
                                               dtype = np.uint16)
                self.m.nextplotmask =  np.zeros([self.reader.sizey, self.reader.sizex], 
                                                dtype = np.uint16)
                
                self.m.UpdatePlots()
                self.button_nextframe.setEnabled(False)
                
            else:
                self.button_nextframe.setEnabled(True)
                self.button_previousframe.setEnabled(True)
                self.m.prevpicture = self.reader.LoadOneImage(self.Tindex-1, self.FOVindex)
                self.m.prevplotmask = self.reader.LoadMask(self.Tindex-1, self.FOVindex)
                   
                self.m.currpicture = self.reader.LoadOneImage(self.Tindex, self.FOVindex)
                self.m.plotmask = self.reader.LoadMask(self.Tindex, self.FOVindex)              
                  
                self.m.nextpicture = self.reader.LoadOneImage(self.Tindex+1,self.FOVindex)
                self.m.nextplotmask = self.reader.LoadMask(self.Tindex+1, self.FOVindex)
                self.m.UpdatePlots()
            
            self.UpdateTitleSubplots()
            self.button_timeindex.clearFocus()
            self.button_timeindex.setText(str(self.Tindex)+'/'+str(self.reader.sizet-1))
            
            if self.button_hidemask.isChecked():
                self.m.HideMask()
            self.EnableCNNButtons()
        
        else:
            self.button_timeindex.clearFocus()
            return
        
     
    def CellCorrespActivation(self):
        self.Disable(self.button_cellcorespondance)
        self.WriteStatusBar('Doing the cell correspondence')

        if self.Tindex != 0:
            self.m.plotmask = self.reader.CellCorrespondence(self.Tindex, self.FOVindex)
            self.m.updatedata()
        else:
            self.m.plotmask = self.reader.LoadSeg(self.Tindex, self.FOVindex)
            self.m.updatedata()

        self.Enable(self.button_cellcorespondance)
        self.m.UpdatePlots()
        self.button_cellcorespondance.setChecked(False)
        self.ClearStatusBar()

    
    def ButtonSaveSegMask(self):
        """saves the segmented mask
        """
        self.reader.SaveSegMask(self.Tindex, self.FOVindex, self.m.plotmask)

        
    def ChangePreviousFrame(self):
         """This function is called when the previous frame buttons is pressed 
         and it tests if the buttons is enabled and if so it calls the
         BackwardTime() function. It should avoid the let the user do multiple 
         clicks and that the function is then called afterwards several times,
         once the frames and masks of the current time index have been loaded.
         """
         if self.button_previousframe.isEnabled():
            self.button_previousframe.setEnabled(False)
            self.BackwardTime()
            if self.Tindex >0:
                self.button_previousframe.setEnabled(True)
         else:
             return
             
             
    def ChangeNextFrame(self):
        """This function is called when the next frame buttons is pressed 
        and it tests if the buttons is enabled and if so it calls the
        ForwardTime() function. It should avoid the let the user do multiple 
        clicks and that the function is then called afterwards several times,
        once the frames and masks of the current time index have been loaded.
        """
        if self.button_nextframe.isEnabled():
            self.button_nextframe.setEnabled(False)
            self.ForwardTime()
            if self.Tindex + 1 < self.reader.sizet:
                self.button_nextframe.setEnabled(True)
                
        else:
            return

        
    def ForwardTime(self):
        """This function switches the frame in forward time index. And it tests
        several conditions if t == lastTimeIndex-1, because then the next frame
        button has to be disabled. It also tests if the show value of cells
        button and hidemask are active in order to hide/show the mask or to 
        show the cell values.
        """
        # the t frame is defined as the currently shown frame on the display.
        # If the button "Next time frame" is pressed, this function is called
        self.WriteStatusBar('Loading the next frame...')
        self.Disable(self.button_nextframe)

        if self.Tindex + 1 < self.reader.sizet - 1 :
            self.reader.SaveMask(self.Tindex, self.FOVindex, self.m.plotmask)
            
            self.m.prevpicture = self.m.currpicture.copy()
            self.m.prevplotmask = self.m.plotmask.copy()
            
            self.m.currpicture = self.m.nextpicture.copy()
            self.m.plotmask = self.m.nextplotmask.copy()
            
            self.m.nextpicture = self.reader.LoadOneImage(self.Tindex+2, self.FOVindex)
            self.m.nextplotmask = self.reader.LoadMask(self.Tindex+2, self.FOVindex)
            self.m.UpdatePlots()

            if self.Tindex + 1 == 1:
                self.button_previousframe.setEnabled(True)
                
        else:
            self.reader.SaveMask(self.Tindex, self.FOVindex, self.m.plotmask)
        
            self.m.prevpicture = self.m.currpicture.copy()
            self.m.prevplotmask = self.m.plotmask.copy()
            self.m.currpicture = self.m.nextpicture.copy()
            self.m.plotmask = self.m.nextplotmask.copy()
            self.m.nextpicture = np.zeros([self.reader.sizey, self.reader.sizex], 
                                          dtype = np.uint16)
            self.m.nextplotmask = np.zeros([self.reader.sizey,self.reader.sizex], 
                                           dtype = np.uint16)
            self.m.UpdatePlots()

            self.button_nextframe.setEnabled(False)

        self.Tindex = self.Tindex+1
        self.UpdateTitleSubplots()
        
        if self.button_hidemask.isChecked():
            self.m.HideMask()

        self.Enable(self.button_nextframe)
        self.ClearStatusBar()
        self.button_timeindex.setText(str(self.Tindex)+'/'+str(self.reader.sizet-1))

    
    def BackwardTime(self):
        """This function switches the frame in backward time index. And it 
        several conditions if t == 1, because then the button previous frame has to
        be disabled. It also tests if the show value of cells button and 
        hidemask are active in order to hide/show the mask or to show the cell
        values.
        """
        # the t frame is defined as the currently shown frame on the display.
        # If the button "Previous time frame" is pressed, this function is called
        self.WriteStatusBar('Loading the previous frame...')
        self.Disable(self.button_previousframe)
        
        self.reader.SaveMask(self.Tindex, self.FOVindex, self.m.plotmask)

        self.m.nextpicture = self.m.currpicture.copy()
        self.m.nextplotmask = self.m.plotmask.copy()
        self.m.currpicture = self.m.prevpicture.copy()
        self.m.plotmask = self.m.prevplotmask.copy()
            
        if self.Tindex == 1:
            self.m.prevpicture = np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
            self.m.prevplotmask = np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
            self.button_previousframe.setEnabled(False)
            
        else:
            self.m.prevpicture = self.reader.LoadOneImage(self.Tindex-2, self.FOVindex)
            self.m.prevplotmask = self.reader.LoadMask(self.Tindex-2, self.FOVindex)

        self.m.UpdatePlots()
        if self.Tindex-1 == self.reader.sizet-2:
            self.button_nextframe.setEnabled(True)            
        
        if self.button_hidemask.isChecked():
            self.m.HideMask()
        
        self.Tindex -= 1
        self.UpdateTitleSubplots()
            
        self.Enable(self.button_previousframe)
        
        if self.Tindex > 0:
            self.button_previousframe.setEnabled(True)          
            
        self.ClearStatusBar()
        self.button_timeindex.setText(str(self.Tindex)+'/' + str(self.reader.sizet-1))


# -----------------------------------------------------------------------------
# MANUAL MASK CORRECTIONS
            
    def ChangeOneValue(self):
        """This function is called when the button Change cell value is
        clicked. It displays the instructions on the status bar.
        And if the user clicks in the graph where the current mask is displayed
        it connects the event of the click (meaning that user has clicked on
        one cell) to the function self.DialogBoxChangeOneValue. 
        This function will then replaces the cell selected by the user with
        the click with a new value entered by the user.
        """
        
        # displaying the instructions on the statusbar
        self.WriteStatusBar((
            'Left-click to select cell, right-click to abort.'))

        # disables all the buttons
        self.Disable(self.button_changecellvalue)
        
        # connects the event "press mouse button" in the matplotlib plot 
        # (picture) to the function self.DialogBoxChangeOneValue
        self.id = self.m.mpl_connect('button_press_event', self.DialogBoxChangeOneValue)
        
        
    def DialogBoxChangeOneValue(self, event):
        """This function is called when the user after the user has selected
        the button Change cell value and clicked in the picture to select
        the desired cell to change.
        
        It first deconnects the mouse click event in matplotlib with this 
        function to not generate any other dialog window.
        
        It then tests if the click is inside the matplotlib plot (if it is
        outside it equals to None) and if it is the current and editable plot
        (the one in the middle of the gui, self.m.ax)
        
        If is true, then it sets the coordinates to int. and creates a dialog
        window where the user is asked to type a value to set it to the cell.
        
        If the user presses ok, it tests if the entry is valid (>0 and not 
        empty) and looks for the old cell value and replaces it. And then
        it updates the plot such that the result of the change can be seen.
        """
        # the function is disconnected from the matplotlib event.
        self.m.mpl_disconnect(self.id)
        
        # test if the button is a left click and if the coordinates
        # chosen by the user click is inside of the current matplotlib plot
        # which is given by self.m.ax
        if (event.button == 1 
            and (event.xdata != None and event.ydata != None) 
            and self.m.ax == event.inaxes):
            newx = int(event.xdata)
            newy = int(event.ydata)
            
            # creates a dialog window
            dlg = cocv.CustomDialog(self)
            
            #if the user presses 'ok' in the dialog window it executes the code
            #else it does nothing
            if dlg.exec_():
                #it tests that the user has entered some value, that it is not
                #empty and that it is equal or bigger to 0.
                if dlg.entry1.text() != '' and int(dlg.entry1.text()) >= 0:
                    #reads the new value to set and converts it from str to int
                    value = int(dlg.entry1.text())
                    
                    # gives the coordinates where it is equal to the value
                    # selected by the user. And it replaces it with the new
                    # value.
                    self.m.plotmask[self.m.plotmask == self.m.plotmask[newy,newx]] = value
                    
                    # updates the plot to see the modification.
                    self.m.updatedata()
                    
        self.Enable(self.button_changecellvalue)
        self.button_changecellvalue.setChecked(False)
        self.m.ShowCellNumbers()
        self.SaveMask()
        self.ClearStatusBar()
        
        
    def DialogBoxECV(self, s):
        """This functions creates from the ExchangeCellValues.py file a 
        window which takes two integer entries and then swaps the cells having
        the given integer values.
        """
        # creates a dialog window from the ExchangeCellValues.py file
        dlg = ecv.CustomDialog(self)
        
        # if the user presses 'ok', it executes the code
        if dlg.exec_():

            # it tests if both value to be swapped are not empty.
            if dlg.entry1.text()!= '' and dlg.entry2.text() != '':
                
                # reads out the values and converts it into integers.
                value1 = int(dlg.entry1.text())
                value2 = int(dlg.entry2.text())
                
                # calls the function which does the swap
                try:
                    self.m.ExchangeCellValue(value1,value2)
                except ValueError as e:
                    QMessageBox.critical(self, 'Error', str(e))
                self.m.ShowCellNumbers()
                self.SaveMask()
        else:
            return


    def MouseDraw(self):
        """
        This function is called whenever the brush or the eraser button is
        pressed. On the first press event it calls the self.m.OneClick, which
        tests whether it is a right click or a left click. If it a right click
        it assigns the value of the pixel which has been right clicked
        to self.cellval, meaning that the next drawn pixels will be set to this
        value.
        If it is left clicked, then it draws a 3x3 square with the current
        value of self.cellval.
        If after left clicking you drag the mouse, then you start drawing 
        using the mouse and it stops once you release the left click.
        
        Same for the eraser button, it sets directly the value of self.cellval
        to 0.
        """
        do_draw = self.button_drawmouse.isChecked()
        do_erase = self.button_eraser.isChecked()
        
        if do_draw or do_erase:
            self.m.tempmask = self.m.plotmask.copy()
            
            if do_draw:
                self.WriteStatusBar(('Draw using the brush, right click to select '
                                     'the cell to draw.'))
                self.Disable(self.button_drawmouse)
                pixmap = QtGui.QPixmap('./icons/brush2.png')
                
            elif do_erase:
                self.WriteStatusBar('Erasing by setting the values to 0.')
                self.Disable(self.button_eraser)
                pixmap = QtGui.QPixmap('./icons/eraser.png')
                self.m.cellval = 0
            
            radius = self.spinbox_brushsize.value()
            self.id2 = self.m.mpl_connect('button_press_event', 
                                          lambda e: self.m.OneClick(e, radius))
            self.id = self.m.mpl_connect('motion_notify_event', 
                                         lambda e: self.m.PaintBrush(e, radius))
            self.id3 = self.m.mpl_connect('button_release_event', self.m.ReleaseClick)
                
            cursor = QtGui.QCursor(pixmap, 0,9)
            QApplication.setOverrideCursor(cursor)
            print('GUI_main if')
                        
        else:
            self.m.mpl_disconnect(self.id3)
            self.m.mpl_disconnect(self.id2)
            self.m.mpl_disconnect(self.id)
            QApplication.restoreOverrideCursor()
            self.Enable(self.button_drawmouse)
            self.Enable(self.button_eraser)
            self.SaveMask()
            self.ClearStatusBar()
            print('GUI_main else')

            
            
    def UpdateTitleSubplots(self):
        """This function updates the title of the plots according to the 
        current time index. So it called whenever a frame or a fov is changed.
        """
        if self.Tindex == 0:
            self.m.titlecurr.set_text('Time index {}'.format(self.Tindex))
            self.m.titleprev.set_text('No frame {}'.format(''))
            self.m.titlenext.set_text('Next time index {}'.format(self.Tindex+1))
            self.m.draw()
            
        elif self.Tindex == self.reader.sizet-1:
            self.m.titlecurr.set_text('Time index {}'.format(self.Tindex))
            self.m.titleprev.set_text('Previous time index {}'.format(self.Tindex-1))
            self.m.titlenext.set_text('No frame {}'.format(''))            
            self.m.draw()
            
        else:
            self.m.titlecurr.set_text('Time index {}'.format(self.Tindex))
            self.m.titleprev.set_text('Previous time index {}'.format(self.Tindex-1))
            self.m.titlenext.set_text('Next time index {}'.format(self.Tindex+1))
            self.m.draw()
        
        
    def ClickNewCell(self):
        """ 
        this method is called when the button New Cell is clicked. If the button
        state corresponds to True (if is activated) then it connects the mouse 
        clicks on the pyqt window to the canvas (so to the matplolib figure).
        The connection has an "id" which is given by the integer self.id
        After the connections is made, it calls the Disable function with argument 0
        which turns off the other button(s).
        
        If the button is clicked but it is deactivated then it disconnects the 
        connection between the canvas and the window (the user can not interact
        with the plot anymore). 
        Storemouseclicks is a list corresponding to the coordinates of all mouse
        clicks between the activation and the deactivation of the button.
        So if it is empty, it does not draw anything because no clicks
        were registered. 
        But if it has some coordinates, it will draw a polygon where the vertices
        are the coordinates of all the mouseclicks.
        Once the figure has been updated with a new polygon, the other button(s)
        are again enabled. 
        
        """
        if self.button_newcell.isChecked():
            self.WriteStatusBar(('Draw a new cell. Use the left click to '
                                 'produce a polygon with a new cell value. '
                                 'Click the button again to confirm.'))
            self.m.tempmask = self.m.plotmask.copy()
            self.id = self.m.mpl_connect('button_press_event', self.m.MouseClick)
            self.Disable(self.button_newcell)
            
        else:
            self.m.mpl_disconnect(self.id)
            if  self.m.storemouseclicks and self.TestSelectedPoints():
                self.m.DrawRegion(True)
            else:
                self.m.updatedata()
            self.Enable(self.button_newcell)
            self.m.ShowCellNumbers()
            self.ClearStatusBar()
            self.SaveMask()
            
            
    def TestSelectedPoints(self):
        """This function is just used to catch an exception, when the new cell
        or the add region function is called. If all the dots drawn by the user
        are located on one line (horizontal or vertical) the DrawRegion 
        function calls a method to create a polygon and 
        it can not make a polygon out of straight line so it gives an error.
        In order to prevent this error, this function avoids to attempt to draw
        by returning False if the square are all on one line.
        """
                
        allx = list(np.array(self.m.storemouseclicks)[:,0])
        ally = list(np.array(self.m.storemouseclicks)[:,1])
        
        resultx = all(elem == allx[0] for elem in allx)
        resulty = all(elem == ally[0] for elem in ally)
        
        if resultx or resulty:
            return False
        else:
            return True
                    
        
    def clickmethod(self):
        """ 
        this method is called when the button Add region is clicked. If the button
        state corresponds to True (if is activated) then it connects the mouse 
        clicks on the pyqt window to the canvas (so to the matplolib figure).
        The connection has an "id" which is given by the integer self.id
        After the connections is made, it calls the Disable function with argument 1
        which turns off the other button(s).
        
        If the button is clicked and it is deactivated then it disconnects the 
        connection between the canvas and the window (the user can not interact
        with the plot anymore). 
        Storemouseclicks is a list corresponding to the coordinates of all mouse
        clicks between the activation and the deactivation of the button.
        So if it is empty, it does not draw anything because no clicks
        were registered. 
        But if it has some coordinates, it will draw a polygon where the vertices
        are the coordinates of all the mouseclicks.
        Once the figure has been updated with a new polygon, the other button(s)
        are again enabled. 
        
        """
        if self.button_add_region.isChecked():
            self.WriteStatusBar(('Select the cell with the first click, '
                                 'then draw polygon with subsequent '
                                 'clicks. Reclick the button to confirm.'))
            self.m.tempmask = self.m.plotmask.copy()
            self.id = self.m.mpl_connect('button_press_event', self.m.MouseClick)           
            self.Disable(self.button_add_region) 
            
        else:
            self.m.mpl_disconnect(self.id)
            
            # test if the list is not empty and if the dots are not all in the same line
            if self.m.storemouseclicks and self.TestSelectedPoints():
                self.m.DrawRegion(False)

            else:
                self.m.updatedata()
                
            self.Enable(self.button_add_region)
            self.m.ShowCellNumbers()
            self.ClearStatusBar()
            self.SaveMask()
            
            
# -----------------------------------------------------------------------------
# BUTTON ENABLE / DISABLE
    
    def Enable(self, button):
         """
         this functions turns on buttons all the buttons, depending on the time
         index. (next and previous buttons should not be turned on if t = 0 
         or t = lasttimeindex)
         """
         for k in range(0, len(self.buttonlist)):
             if button != self.buttonlist[k]:
                 self.buttonlist[k].setEnabled(True)
                 
         if self.Tindex == 0:
             self.button_previousframe.setEnabled(False)
             
         if self.Tindex == self.reader.sizet-1:
             self.button_nextframe.setEnabled(False)
             
         self.EnableCNNButtons()
         
     
    def Disable(self, button):
         """
         this functions turns off all the buttons except the one given in 
         argument.
         """

         for k in range(0,len(self.buttonlist)):
             if button != self.buttonlist[k]:
                 self.buttonlist[k].setEnabled(False)


    def EnableCNNButtons(self):
        if self.reader.TestTimeExist(self.Tindex, self.FOVindex):
            self.button_cellcorespondance.setEnabled(True)
            self.button_extractfluorescence.setEnabled(True)
        else:
            self.button_cellcorespondance.setEnabled(False)
            self.button_extractfluorescence.setEnabled(False)
    
    
    def EnableCorrectionsButtons(self):
        self.button_newcell.setEnabled(True)
        self.button_add_region.setEnabled(True)
        self.button_drawmouse.setEnabled(True)
        self.button_eraser.setEnabled(True)
        self.button_exval.setEnabled(True)
        self.button_changecellvalue.setEnabled(True)
        self.button_showval.setEnabled(True)
        
        
    def DisableCorrectionsButtons(self):
        self.button_newcell.setEnabled(False)
        self.button_add_region.setEnabled(False)
        self.button_drawmouse.setEnabled(False)
        self.button_eraser.setEnabled(False)
        self.button_exval.setEnabled(False)
        self.button_changecellvalue.setEnabled(False)
        self.button_showval.setEnabled(False)

    
    def SaveMask(self):
        """
        When this function is called, it saves the current mask
        (self.m.plotmask)
        """
        self.reader.SaveMask(self.Tindex, self.FOVindex, self.m.plotmask)
        
        
    def WriteStatusBar(self, text):
        """Writes text to status bar"""
        self.statusBarText.setText(text)
        
        
    def ClearStatusBar(self):
        """Removes text from status bar"""
        self.statusBarText.setText('')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # If two arguments are given, make them nd2name and hdfname
    if len(sys.argv)==3:
        nd2name1 = sys.argv[1]
        hdfname1 = sys.argv[2]
        ex = App(nd2name1, hdfname1, '')
        sys.exit(app.exec_())
    
    # Launch file browser otherwise
    else:
        wind = dfb.FileBrowser()
        if wind.exec_():
            nd2name1 = wind.nd2name
            hdfname1 = wind.hdfname
            hdfnewname = wind.newhdfentry.text()
            ex = App(nd2name1, hdfname1, hdfnewname)
            sys.exit(app.exec_())
        else:
            app.exit()
        
