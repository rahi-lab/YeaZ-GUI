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
If the user is happy with the segmentation, the Cell Correspondance button 
can be clicked. Until then, the cells get random numbers attributed by
the segmentation algorithm. In order to keep track of the cell through time,
the same cells should have the same number between two different time pictures.
This can be (with some errors) achieved by the Cell Correspondance button,
which tries to attribute the same number to corresponding cells in time.
After that, the final mask is saved and it is always visible when you go on
the corresponding picture. This mask can also be corrected using the 
usual buttons (because the Cell Correspondance makes also mistakes). 

"""

import sys
#append all the paths where the modules are stored. Such that this script
#looks into all of these folders when importing modules.
sys.path.append("./unet")
sys.path.append("./disk")
sys.path.append("./icons")
sys.path.append("./init")
sys.path.append("./misc")
import numpy as np


# Import everything for the Graphical User Interface from the PyQt5 library.
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QSizePolicy, \
    QMessageBox, QPushButton, QCheckBox, QAction, QStatusBar
from PyQt5 import QtGui

#Import from matplotlib to use it to display the pictures and masks.
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
import matplotlib.pyplot as plt

#import the colormaps function to create a customed colormap scale with 10 
#colors only
from matplotlib import cm
from matplotlib.colors import ListedColormap
#import Path functions to handle the regions drawn by the user. ("add region
#and new cell")
from matplotlib.path import Path
 

#Import all the other python files
#this file handles the interaction with the disk, so loading/saving images
#and masks and it also runs the neural network.
import InteractionDisk_temp as nd


#this file contains a dialog window that takes two integers as entry to swap
#two cell values
import ExchangeCellValues as ecv
#this file contains a dialog window which is opened before the main program
#and allows to load the nd2 and hdf files by browsing through the computer.
import DialogFileBrowser as dfb
#this file contains a window that opens to change the value of one cell. It 
#is opened as soon as the user presses with the left click on a specific cell.
import ChangeOneCellValue as cocv
#this file contains a dialog window to browse for the excel file where
#all the extracted information on the fluoerscence is written. Or to create a 
#new excel file by typing a name in the text box. It is thought to have one 
#excel file per field of view.
import DialogDataBrowser as ddb
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


import random

#import everything needed to write and read excel files.
from openpyxl import load_workbook
from openpyxl import Workbook


#def show_error(msg):
#    error_dialog = QErrorMessage()
#    error_dialog.showMessage(msg)
#    error_dialog.exec_
    


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
#        initializes the window
#       set a title to the window
        self.title = 'YeaZ 1.0'

#        id is an integer that gives the id of the connection between the mouseclick method
#        and the activation of the button.

#       all these ids are integers which are used to set a connection between
#       the button and the function that this button calls.
#       There are three of them because it happens that one can trigger three 
#       different functions with one button.        
        self.id = 0
        self.id2 = 0
        self.id3 = 0 



#       it calls an object of the class Load Image from the InteractionDisk
#       file which is used to load images and masks from the nd2 file or tiff files. To
#       initialize this object it needs the path of the nd2 file, of an
#       existing hdf file and the name of a new hdf file. If the user has no
#       hdf file yet the hdfpathstr will be empty and vice versa if the user
#       selects an already existing hdf file.
#       It takes all the strings given by the first window 
#       (called before the main window opens) from the DialogFileBrowser.py 
#       file. (see at the end of this code)

        self.reader = nd.Reader(hdfpathstr, newhdfstr, nd2pathstr)
        
        
#       these variables are used to create/read/load the excel file used
#       to write the fluorescence values extracted. For each field of view,
#       the user will be asked each time to create a new xls file for the 
#       field of view or to load an existing field of view (this is the role
#       of the boolean variable)
        self.xlsfilename = ''
        self.nd2path = nd2pathstr
        self.FlagFluoExtraction = False

        
        
        
#        Set the indices for the time axis and the field of view index. These
#        indices represent everywhere the current picture (the one that can be
#        edited, i.e. the time t frame)
        self.Tindex = 0
        self.FOVindex = 0
        
#        loading the first images of the cells from the nd2 file
        self.currentframe = self.reader.LoadOneImage(self.Tindex,self.FOVindex)
        
        #check if the t+1 time frame exists, avoid failure if there is only
        #one picture in the folder/nd2 file
        if self.Tindex+1 < self.reader.sizet:
            self.nextframe = self.reader.LoadOneImage(self.Tindex+1, self.FOVindex)
        else:
            self.nextframe = np.zeros([self.reader.sizey, self.reader.sizex])
        
        self.previousframe = np.zeros([self.reader.sizey, self.reader.sizex])
        
        

#        loading the first masks from the hdf5 file
        self.mask_curr = self.reader.LoadMask(self.Tindex, self.FOVindex)
        self.mask_previous = np.zeros([self.reader.sizey, self.reader.sizex])
        
        #check if the t+1 mask exists, avoid failure if there is only
        #one mask in the hdf file
        if self.Tindex+1 < self.reader.sizet:
            self.mask_next = self.reader.LoadMask(self.Tindex+1, self.FOVindex)
        else:
            self.mask_next = np.zeros([self.reader.sizey, self.reader.sizex])
        

    
#        creates a list of all the buttons, which will then be used in order
#        to disable all the other buttons at once when one button/function
#        is pressed/used in the gui.
        self.buttonlist = []
        
        
#        setting buttons as attributes
#        the shortcuts for the buttons, the functions to which they are
#        connected to,... are all set up in the ButtonInit file which is called
#        in the self.initUI() method below.
        
        self.button_newcell = QPushButton("New cell")
        self.buttonlist.append(self.button_newcell)
        
        self.button_add_region = QPushButton("Add region")
        self.buttonlist.append(self.button_add_region)
        
        self.button_savemask = QPushButton("Save Mask")
        self.buttonlist.append(self.button_savemask)
        
        self.button_drawmouse = QPushButton('Brush')
        self.buttonlist.append(self.button_drawmouse)
        
        self.button_eraser = QPushButton('Eraser')
        self.buttonlist.append(self.button_eraser)
        
        self.button_exval = QPushButton('Exchange Cell Values')
        self.buttonlist.append(self.button_exval)
        
        self.button_showval = QCheckBox('Show Cell Values')
        self.buttonlist.append(self.button_showval)
        
        self.button_hidemask = QCheckBox('Hide Mask')
        self.buttonlist.append(self.button_hidemask)
        
        self.button_nextframe = QPushButton("Next Time Frame")
        self.buttonlist.append(self.button_nextframe)
        
        self.button_previousframe = QPushButton("Previous Time Frame")
        self.buttonlist.append(self.button_previousframe)
        
        self.button_cnn = QPushButton('Launch CNN')
        self.buttonlist.append(self.button_cnn)
        
        self.button_threshold = QCheckBox('Threshold prediction')
        self.buttonlist.append(self.button_threshold)
        
        self.button_segment = QCheckBox('Segment')
        self.buttonlist.append(self.button_segment)
                 
        self.button_cellcorespondance = QPushButton('Tracking')
        self.buttonlist.append(self.button_cellcorespondance)
        
        self.button_changecellvalue = QPushButton('Change cell value')
        self.buttonlist.append(self.button_changecellvalue)        
        
        self.button_extractfluorescence = QPushButton('Extract Fluorescence')
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

#       Here our canvas is created where using matplotlib, 
#       one can plot data to display the pictures and masks.
        self.m = PlotCanvas(self)
        
#       Initialize all the buttons that are needed and the functions that are 
#       connected when the buttons are triggered.
        InitButtons.Init(self)
        InitLayout.Init(self)
        
#        MENU, TOOLBAR AND STATUS BAR
#       creates a menu just in case, some other functions can be added later
#        in this menu.
        menubar = self.menuBar()
        self.fileMenu = menubar.addMenu('File')   
        self.saveactionmenu = QAction('Save')
        self.fileMenu.addAction(self.saveactionmenu)
        self.saveactionmenu.triggered.connect(self.ButtonSaveMask)

        
#       hide the toolbar and instead of the original buttons of matplotlib,
#       QPushbuttons are used and are connected to the functions of the toolbar
#       it is than easier to interact with these buttons (for example to 
#       to disable them and so on..)
        self.Nvgtlbar = NavigationToolbar(self.m, self)
        self.addToolBar(self.Nvgtlbar)
        self.Nvgtlbar.hide()
        
#        creates a status bar, which displays (or should display) some text
#        whenever a function is used.
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
                
        self.show()
                
    
    def mousePressEvent(self, QMouseEvent):
        """this function is implemented just to have the QLineButtons of the 
        change time index button, setthreshold button and the setsegmentation
        button out of focus when the user clicks somewhere
        on the gui. (to unfocus the buttons)
        """
        self.button_timeindex.clearFocus()
        if self.button_SetThreshold.isEnabled():
            self.button_SetThreshold.clearFocus()
            
        if self.button_SetSegmentation.isEnabled():
            self.button_SetSegmentation.clearFocus()
        
        
        
#        CONNECT the functions of the toolbar to our custom QPushbuttons.
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
        
        if self.button_zoom.isChecked() and not(self.button_segment.isChecked() or self.button_threshold.isChecked()):
            self.Disable(self.button_zoom)
            
        elif self.button_zoom.isChecked() and self.button_segment.isChecked():
            self.Disable(self.button_zoom)
            self.button_segment.setEnabled(True)
            
        elif self.button_zoom.isChecked() and self.button_threshold.isChecked():
            self.Disable(self.button_zoom)
            self.button_threshold.setEnabled(True)
            
        elif self.button_zoom.isChecked() == False and self.button_segment.isChecked():
            
            self.button_pan.setEnabled(True)
            self.button_home.setEnabled(True)
            self.button_back.setEnabled(True)
            self.button_forward.setEnabled(True)
            
            self.EnableCorrectionsButtons()
            
        elif self.button_zoom.isChecked() == False and self.button_threshold.isChecked():
            
            self.button_pan.setEnabled(True)
            self.button_home.setEnabled(True)
            self.button_back.setEnabled(True)
            self.button_forward.setEnabled(True)
            
        else:
            self.Enable(self.button_zoom)
        
    def HomeTlbar(self):
#        connects the home button to the home function of the matplotlib
#        toolbar. It sets the view to the original view (no zoom)
        self.Nvgtlbar.home()

            
    def BackTlbar(self):
#        It calls the back function of the matplotlib toolbar which sets the 
#        view to the previous one (if the user does several zooms/pans, 
#        this button allows to go back in the "history of views")
        self.Nvgtlbar.back()

        
        
    def ForwardTlbar(self):
#        It calls the forward function of the matplotlib toolbar which sets the 
#        view to the next one (if the user does several zooms/pans, 
#        this button allows to go forward in the "history of views"
        
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

        if self.button_pan.isChecked() and not(self.button_segment.isChecked() or self.button_threshold.isChecked()):
            self.Disable(self.button_pan)
            
        elif self.button_pan.isChecked() and self.button_segment.isChecked():
            self.Disable(self.button_pan)
            self.button_segment.setEnabled(True)
            
        elif self.button_pan.isChecked() and self.button_threshold.isChecked():
            self.Disable(self.button_pan)
            self.button_threshold.setEnabled(True)
            
        elif not(self.button_pan.isChecked()) and self.button_segment.isChecked():
            
            self.button_zoom.setEnabled(True)
            self.button_home.setEnabled(True)
            self.button_back.setEnabled(True)
            self.button_forward.setEnabled(True)
            
            self.EnableCorrectionsButtons()
            
        elif not(self.button_pan.isChecked()) and self.button_threshold.isChecked():
            self.button_zoom.setEnabled(True)
            self.button_home.setEnabled(True)
            self.button_back.setEnabled(True)
            self.button_forward.setEnabled(True)

        
        else:
            self.Enable(self.button_pan)


    def ButtonFluo(self):
        """This function is called everytime the Extract Fluorescence button is 
        clicked (self.button_extractfluorescence). 
        
        self.FlagFluoExtraction is boolean which is True when the path to the 
        excel file has already been loaded into self.xlsfilename.
        This pathname changes for each field of view as it is thought to have
        one xls file per field of view. 
        So at the beginning and each time the user changes field of view,
        self.FlagFluoExtraction is set to False.
        
        When it is set to False, this function calls a dialog window where
        the user is asked to load an already existing xls file for the current
        field of view or to give a name to create a new xls file for
        the current field of view. (self.Dialogxls)
        
        If it set to true, it means that self.xlsfilename contains the path
        to the xls file for the current field of view and it is directly given
        to the function that writes the fluorescence into the xls file.
        (self.ExtractFluo)
        """
        
        if self.FlagFluoExtraction:
            self.ExtractFluo(self.xlsfilename)
        else:
            self.DialogXls()
        
        
    def DialogXls(self):
        """This function creates a dialog window which gives two options to the
        user either to load an existing xls file or to give a new name in order
        to create a new xls file. 
        """
#        creates the window
        dwind = ddb.FileBrowser()

#        this test is True if the user presses ok in the dialog window, if the 
#        user presses cancels it returns and nothing happens.
        
        if dwind.exec_():
            
#            read the entry given by the file browser
            xlsname = dwind.xlsname
            
#            reads the entry given by the new filename text field.
            newxlsname = dwind.newxlsentry.text()

#            if the string containing the filepath to an existing xls file 
#            is not empty then it calls directly the function to write the 
#            data into this existing xls file and sets self.xlsfilename
            if xlsname:
                
                self.xlsfilename = xlsname
                self.ExtractFluo(xlsname)
                
#           if xlsname is empty then it creates a new pathfilename and puts
#           the new created xls file into the folder where nd2 is located.
#           the string containing the nd2 namepath is split
            else:
                xlsname = ''
                templist = self.nd2path.split('/')
                
                for k in range(0, len(templist)-1):
                    
                    xlsname = xlsname + templist[k] + '/'
#               this is the new path/filename
                xlsname = xlsname + newxlsname + '.xlsx'
                self.xlsfilename = xlsname
                
#               here as a new name has been given, it means that a new xls file
#                should be created, this is done with CreateXls
                self.CreateXls(xlsname)
#                once there is an existing xls file, it writes in this file
#                using self.ExtractFluo.
                self.ExtractFluo(xlsname)
#           this flag is set to true, for the current field of view each
#           time extract fluorescence is clicked it writes in the file located
#           at self.xlsfilename.
            self.FlagFluoExtraction = True
        else:
            
            return


    def CreateXls(self, xlsfilename):
        """In case there is no xls file existing, here a new one is created 
        and prepared. For each channel a new sheet is created.
        In the first row for each sheet, the time indices are written t = 0,
        t = 1, etc... but only every third column. Because in the row below,
        three values are extracted 'Total intensity', 'Area' and 'Variance'
        at each time index. So three columns for each time index are needed,
        for the three data points. 
        The first column is left empty (starting from third row) because
        the cell numbers will be written in there.
        """
        
#        creates a new xls file using xlwt library.
        book = Workbook()
        nbrchannels = self.reader.sizec
        
        for i in range(0,nbrchannels):
            sheetname = self.reader.channel_names[i]
#            creates a sheet with the name of the corresponding channel.
            if i == 0:
                sheet = book.active
                sheet.title = sheetname
            else:
                sheet = book.create_sheet(sheetname)
            sheet.cell(1,1, 'Cell Number / Time axis')
            sheet.cell(2,1, 'labels')
            timeaxissize = self.reader.sizet
#           start writing the time index at column 1, column 0 is reserved for
#           cell numbers.
            timecolindex = 2
            
            for t in range(1,timeaxissize+1):
#                in row 0 the time index is written
                sheet.cell(1,timecolindex).value = 't = {}'.format(t-1)
#                in row 1, the label of the three data points are written
                sheet.cell(2,timecolindex).value = 'Total Intensity'
                sheet.cell(2,timecolindex+1).value = 'Total Area'
                sheet.cell(2,timecolindex+2).value = 'Mean Intensity'
                sheet.cell(2,timecolindex+3).value =  'Variance'
#                updates the index, where the next time index should be written
                timecolindex = timecolindex + 4
              
#       saves the xls file.
        print(xlsfilename)
        try:
            book.save(xlsfilename)
            break
        except TypeError:
            QMessageBox.critical(self, "Error", "TypeError encountered. \
                                 Make sure you have openpyxl version 3.0.1 \
                                 installed. If the problem persists contact \
                                 the developers.")



        
    def ExtractFluo(self, xlsfilename):
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
        
#        disables all the buttons except the one passed in argument.
        self.Disable(self.button_extractfluorescence)
#        shows a message on the status bar to show that the program is working
        self.statusBar.showMessage('Extracting the fluorescence...')
        
#        opens the file to read it.
        book = load_workbook(self.xlsfilename)

#       makes a copy of the reading file to write in it the new values.
#        wb = xlscopy(readbook) # a writable copy (can't read values out of this, only write to it)

#        iterate over all the channels, so over all the sheets in the file
        for channel in range(0, self.reader.sizec):
#           loads the picture corresponding to the channel, time index and fov
            image = self.reader.LoadImageChannel(self.Tindex, self.FOVindex, channel)
            
#            loads the sheet to read out corresponding to the current channel
            sheet = book.worksheets[channel]
#            sheet = readbook.sheet_by_index(channel)
            
#            this line is here to prevent some errors of streaming into
#            the file due to read file which is open (I am not sure about this
#            but it is a more or less working solution found on stackoverflow)
#            os.remove(xlsfilename)
            
#           load the sheet corresponding to the current channel to write in it
#            writingsheet = wb.get_sheet(channel)
            
#           this index contains the value of the maximum number of rows in the
#           file, it is used to append at the end the cell number column a new
#           cell/value, and it is updated each time a new cell is added.
            tempidx = sheet.max_row
           
#           np.unique(array) returns an array which contains all the value
#           that appear in self.m.plotmask, so it returns every cell value
#           including the background (value 0) present in self.m.plotmask
            for val in np.unique(self.m.plotmask):
                
#                exclude the background, as it is not a cell
                if val != 0:
                    
#                    this (self.m.plotmask==val).sum() adds one at every pixel
#                    where self.m.plotmask has the value val
                    area = (self.m.plotmask == val).sum()
#                    it sums the value of the pixel in image at the coordinates
#                    where self.m.plotmask equals val.
                    tot_intensity = image[self.m.plotmask == val].sum()
                    
#                    calculate the mean to use it in the calc. of the variance.
                    mean = tot_intensity/area
                    
#                    create a copy of plotmask because I had weird experiences
#                    with np.where where it modified sometimes the given array
#                    (not sure)
                    temparr = self.m.plotmask.copy()

#                    extract the coordinates of the mask matrix where it equals 
#                    the current cell value val
                    coord = np.where(temparr == val)
                    
#                    variable to save the variance.
                    var = 0
                    
#                    we loop over the coord of the pixel where mask == val
                    for i in range(0,len(coord[0])):
#                        extract the intensity at the coordinate
                        val_intensity = image[coord[0][i], coord[1][i]]
#                        substract the value of the intensity with the mean,
#                        and square it. It is then add to the var.
                        var = var + (val_intensity-mean)*(val_intensity-mean)
                        
#                   var is then divided by the number of the pixel
#                   corresponding to this value (also equal to the area)
#                   to get the variance.
                    var = var/area

#                    if flag is false it means that the cell number
#                    corresponding to val is not present in the xls file, first
#                    column.
                    flag = False
                    
                    
#                    iterate over all the rows
                    for row in range(sheet.max_row+1):
                        
#                        test if in the first column 0, the number of the cell
#                        is already present
#                         if sheet.cell_value(row,0) == str(val):
                         if sheet.cell(row = row+1, column = 1).value == str(val):
                             
#                             if is present, the column corresponding to the
#                             current time index is by iterating over the cols.
                             for col in range(sheet.max_column+1):
#                                 test if it is the right column
#                                 if sheet.cell_value(0, col) == 't = {}'.format(self.Tindex):
                                 if sheet.cell(row = 1, column = col+1).value == 't = {}'.format(self.Tindex):
#                                   write in the xls file at the row, col coord
                                     sheet.cell(row+1, col+1, str(tot_intensity))
                                     sheet.cell(row+1, col+2, str(area))
                                     sheet.cell(row+1,col+3, str(mean))
                                     sheet.cell(row+1, col+4, str(var))
                                     book.save(xlsfilename)


#                                     the flag is set to True so that it does
#                                     not execute the code where the cell is
#                                     added in the xls file in a new row.
                                     flag = True
                    if not flag:
#                    this lines are executed if a new cell is detected or if
#                    if it is the first time to write in the file.
                        for col in range(sheet.max_column+1):
                            if sheet.cell(row = 1, column =  col+1).value == 't = {}'.format(self.Tindex):
#                                it write the cell value/cell number in the
#                                column
                                sheet.cell(tempidx+1,1, str(val))
                                
#                                writes the data extracted before
                                sheet.cell(tempidx+1,col+1,str(tot_intensity))
                                sheet.cell(tempidx+1, col+2, str(area))
                                sheet.cell(tempidx+1, col+3, str(mean))
                                sheet.cell(tempidx+1, col+4, str(var))
#                                it updates the number of rows as a new cell
#                                has been added, so there is one more row.
                                tempidx = tempidx + 1
#                               save in the file
                                book.save(xlsfilename)

                    
#       Enable again all the buttons          
        self.Enable(self.button_extractfluorescence)
        
#        clear the message shown in the status bar
        self.statusBar.clearMessage()

    
    def ShowHideCNNbuttons(self):
        
        """hide and show the buttons corresponding to the neural network.
            this function is called by the button CNN which is hidden. But
            if activated in the InitLayout.py then you can have a button
            which hides the CNN buttons (which are now on the normal also
            hidden...).
        """
        
        
        if self.button_hide_show.isChecked():
            
            
            self.button_cnn.setVisible(True)
            self.button_segment.setVisible(True)
            self.button_savesegmask.setVisible(True)
            self.button_threshold.setVisible(True)
            self.button_SetThreshold.setVisible(True)
            self.button_savethresholdmask.setVisible(True)
            self.button_SetSegmentation.setVisible(True)



        
        else:
            

            self.button_cnn.setVisible(False)
            self.button_segment.setVisible(False)
            self.button_savesegmask.setVisible(False)
            self.button_threshold.setVisible(False)
            self.button_SetThreshold.setVisible(False)
            self.button_savethresholdmask.setVisible(False)
            self.button_SetSegmentation.setVisible(False)
            

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
#        creates a dialog window from the LaunchBatchPrediction.py file
        dlg = lbp.CustomDialog(self)
        
#        this if tests if the user pressed 'ok' in the dialog window
        if dlg.exec_() == QDialog.Accepted:
            
    #       it tests if the user has entered some values
    #       if not it ignores and returns.
            if not (dlg.entry1.text()!= '' and dlg.entry2.text() != ''):
                QMessageBox.critical(self, "Error", "No Time Specified")
                return 
    #       reads out the entry given by the user and converts the index
    #       to integers
            time_value1 = int(dlg.entry1.text())
            time_value2 = int(dlg.entry2.text())
    
    
    #                it tests if the first value is smaller or equal such that
    #                time_value1 is the lower range of the time range
    #                and time_value2 the upper boundary of the range.
            if time_value1 > time_value2 :
                QMessageBox.critical(self, "Error", 'Invalid Time Constraints')
                return
            
            
            
            # displays that the neural network is running
            self.statusBar.showMessage('Running the neural network...')
    
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
                    
                    self.PredThreshSeg(t, dlg.listfov.row(item), thr_val, seg_val)
                    
                    # if tracker has been checked then apply it
                    
                    if dlg.tracking_checkbox.isChecked():
                        
                        if t != 0:
                        
                            temp_mask = self.reader.CellCorrespondance(t,dlg.listfov.row(item))
                            self.reader.SaveMask(t,dlg.listfov.row(item), temp_mask)
                        
                        else:
                            
                            temp_mask = self.reader.LoadSeg(t, dlg.listfov.row(item))
                            self.reader.SaveMask(t,dlg.listfov.row(item), temp_mask)
                            
                        
            
            self.ReloadThreeMasks()
               
            #once it has iterated over all the fov, the message in 
            #the status bar is cleared and the buttons are enabled.
            self.statusBar.clearMessage()
            self.EnableCNNButtons()
   
    
    def PredThreshSeg(self, timeindex, fovindex, thr_val, seg_val):
          """
          This function is called in the LaunchBatchPrediction function.
          This function calls the neural network function in the
          InteractionDisk.py file and then thresholds the result
          of the prediction, saves this thresholded prediction.
          Then it segments the thresholded prediction and saves the
          segmentation. 
          """
#          launches the neural network
          self.reader.LaunchPrediction(timeindex, fovindex)
#          thresholds the prediction
          self.m.ThresholdMask = self.reader.ThresholdPred(thr_val, timeindex,fovindex)
#          saves the thresholded pred.
          self.reader.SaveThresholdMask(timeindex, fovindex, self.m.ThresholdMask)
#          segments the thresholded pred.
          self.m.SegmentedMask = self.reader.Segment(seg_val, timeindex,fovindex)
#          saves the segmentation
          self.reader.SaveSegMask(timeindex, fovindex, self.m.SegmentedMask)
    
    
    def LaunchPrediction(self):
        """This function is not used in the gui, but it can be used to launch
        the prediction of one picture, with no thresholding and no segmentation
        """
        if not(self.reader.TestPredExisting(self.Tindex, self.FOVindex)):
            self.statusBar.showMessage('Running the neural network...')
            self.Disable(self.button_cnn)
            self.reader.LaunchPrediction(self.Tindex, self.FOVindex)
            
            self.Enable(self.button_cnn)
            
            self.button_cnn.setEnabled(False)
            self.button_threshold.setEnabled(True)
            self.button_segment.setEnabled(True)
            self.button_cellcorespondance.setEnabled(True)
            self.statusBar.clearMessage()
        
    def ChangeOneValue(self):
        """This function is called when the button Change cell value is
        clicked. It displays the instructions on the status bar.
        And if the user clicks in the graph where the current mask is displayed
        it connects the event of the click (meaning that user has clicked on
        one cell) to the function self.DialogBoxChangeOneValue. 
        This function will then replaces the cell selected by the user with
        the click with a new value entered by the user.
        """
        
#        displaying the instructions on the statusbar
        self.statusBar.showMessage('Select one cell using the left click and then enter the desired value in the dialog box')

#       disables all the buttons
        self.Disable(self.button_changecellvalue)
        
#        connects the event "press mouse button" in the matplotlib plot 
#       (picture) to the function self.DialogBoxChangeOneValue
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
        
#        the function is disconnected from the matplotlib event.
        self.m.mpl_disconnect(self.id)
        
#        test if the button is a left click and if the coordinates
#        chosen by the user click is inside of the current matplotlib plot
#        which is given by self.m.ax
        if event.button == 1 and (event.xdata != None and event.ydata != None) and self.m.ax == event.inaxes:
            newx = int(event.xdata)
            newy = int(event.ydata)
            
#            creates a dialog window
            dlg = cocv.CustomDialog(self)
            
#            if the user presses 'ok' in the dialog window it executes the code
#           else it does nothing
            if dlg.exec_():
#                it tests that the user has entered some value, that it is not
#                empty and that it is equal or bigger to 0.
                if dlg.entry1.text() != '' and int(dlg.entry1.text()) >= 0:
#                    reads the new value to set and converts it from str to int
                    value = int(dlg.entry1.text())
                    
#                    self.m.plotmask[newy, newx] the value selected by the user
#                    self.m.plotmask == self.m.plotmask[newy, newx]
#                    gives the coordinates where it is equal to the value
#                    selected by the user. And it replaces it with the new
#                    value.
                    self.m.plotmask[self.m.plotmask == self.m.plotmask[newy,newx]] = value
#                    updates the plot to see the modification.
                    self.m.updatedata()
                    
#                   if the button to show cell values is checked, then it
#                   replots the cell values
        
                    if self.button_showval.isChecked():
                        self.m.ShowCellNumbersCurr()
                        self.m.ShowCellNumbersNext()
                        self.m.ShowCellNumbersPrev()

#       enables the button again
        self.Enable(self.button_changecellvalue)
        
#        clears the message in the status bar
        self.statusBar.clearMessage()
        

        
#        the button is a checkable and it has to be unchecked else it seems
#        that the button is still in use, because it gets a blue color.
        self.button_changecellvalue.setChecked(False)

        
        
        
    def DialogBoxECV(self, s):
        """This functions creates from the ExchangeCellValues.py file a 
        window which takes two integer entries and then swaps the cells having
        the given integer values.
        """
#        creates a dialog window from the ExchangeCellValues.py file
        dlg = ecv.CustomDialog(self)
        
#        if the user presses 'ok', it executes the code
        if dlg.exec_():

#            it tests if both value to be swapped are not empty.
            if dlg.entry1.text()!= '' and dlg.entry2.text() != '':
                
#                reads out the values and converts it into integers.
                value1 = int(dlg.entry1.text())
                value2 = int(dlg.entry2.text())
                
#                calls the function which does the swap
                self.m.ExchangeCellValue(value1,value2)
                
#                if the button to display the values of the cell is checked,
#                the values are again displayed on the graph after the swap
#                of cells.
                if self.button_showval.isChecked():
                    self.m.ShowCellNumbersCurr()
                    self.m.ShowCellNumbersNext()
                    self.m.ShowCellNumbersPrev()

            
        else:
            return
    
    
    
    def SelectChannel(self, index):
        """This function is called when the button to select different channels
        is used. From the displayed list in the button, the chosen index
        corresponnds to the same index in the list of channels from the reader.
        So, it sets the default channel with the new index (called index below)
        """
        
#        This function attributes the FOV chosen by the user corresponding to
#        the index in the list of options.
        self.reader.default_channel = index
#        update the pictures using the same function as the one used to 
#        change the fields of view.
        self.ChangeFOV()
        



    def SelectFov(self, index):
        """This function is called when the button containing the list of 
        fields od view is used.
        The index correspondds to the field of view selected in the list.
        
        """
        
#        This function attributes the FOV chosen by the user corresponding to
#        the index in the list of options. First the mask is automatically
#        saved.
        self.reader.SaveMask(self.Tindex, self.FOVindex, self.m.plotmask)
#        the new index is set.
        self.FOVindex = index    
        
#        it updates the fov in the plot with the new index.
        self.ChangeFOV()
        
#        the flag of the fluorescence extraction is set to False (such that
#        if the user extracts fluorescence data in the new field of  view,
#        there is a dialog box asking to select the corresponding xls file
#        for this field of view. IF there is no data sheet for this fov, the
#        user can enter a new name to make a new file.)
        self.FlagFluoExtraction = False
        
    def ChangeFOV(self):
        
#        it changes the fov or channel according to the choice of the user
#        and it updates the plot shown and it initializes the new fov/channel
#        at t=0 by default.
        
#        set the time index to 0
        self.Tindex = 0
        
#        load the image and mask for the current plot
        self.m.currpicture = self.reader.LoadOneImage(self.Tindex,self.FOVindex)
        self.m.plotmask = self.reader.LoadMask(self.Tindex,self.FOVindex)
        
#        sets the image and the mask to 0 for the previous plot
        self.m.prevpicture = np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
        self.m.prevplotmask = np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
        
#        load the image and the mask for the next plot, check if it exists
        if self.Tindex+1 < self.reader.sizet:
            self.m.nextpicture = self.reader.LoadOneImage(self.Tindex+1, self.FOVindex)
            self.m.nextplotmask = self.reader.LoadMask(self.Tindex+1, self.FOVindex)
            #       enables the next frame button in case it was disabled when the 
            #        fov/channel was changed
            self.button_nextframe.setEnabled(True)
        else:
            self.m.nextpicture = np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
            self.m.nextplotmask =  np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
            #       disables the next frame button if the mask or the picture
            # does not exist.
            self.button_nextframe.setEnabled(False)
            
#        once the images and masks are loaded into the variables, they are 
#        displaye in the gui.
        self.m.UpdateBckgrndPicture()
        
#        disables the previous frame button in case it was active before 
#        changing fov/channel.
        self.button_previousframe.setEnabled(False)
        
#        updates the title of the plots to display the right time indices
#        aboves the plots.
        self.UpdateTitleSubplots()

#       if the button to show cell values is active, it shows the values again.
        if self.button_showval.isChecked():
            self.m.ShowCellNumbersCurr()
            self.m.ShowCellNumbersNext()
            self.m.ShowCellNumbersPrev()
            
#       if the button to hide the mask was checked before changing fov/channel,
#       it hides the mask again.
        if self.button_hidemask.isChecked():
            self.m.HideMask()
        
#        the button to set the time index is also set to 0/default again.
        self.button_timeindex.setText('')
#        enables the neural network buttons if there is already an 
#        existing prediction for the current image.
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
    
    
                self.m.UpdateBckgrndPicture()
                self.button_previousframe.setEnabled(False)
                
                
            elif self.Tindex == self.reader.sizet-1:
                self.button_previousframe.setEnabled(True)
                
                self.m.prevplotmask = self.reader.LoadMask(self.Tindex-1, self.FOVindex)
                   
               
                self.m.plotmask = self.reader.LoadMask(self.Tindex, self.FOVindex)
                  
                  
                
                self.m.nextplotmask =  np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
                
                self.m.UpdateBckgrndPicture()
                self.button_nextframe.setEnabled(False)
                
            
            else:
                
                self.button_nextframe.setEnabled(True)
                self.button_previousframe.setEnabled(True)
                
                self.m.prevplotmask = self.reader.LoadMask(self.Tindex-1, self.FOVindex)
                   
               
                self.m.plotmask = self.reader.LoadMask(self.Tindex, self.FOVindex)              
                  
                
                self.m.nextplotmask = self.reader.LoadMask(self.Tindex+1, self.FOVindex)
                
                self.m.UpdateBckgrndPicture()
            
            self.UpdateTitleSubplots()

            
            if self.button_showval.isChecked():
                self.m.ShowCellNumbersCurr()
                self.m.ShowCellNumbersNext()
                self.m.ShowCellNumbersPrev()
            
            if self.button_hidemask.isChecked():
                self.m.HideMask()
            self.EnableCNNButtons()
        
        else:

            return
        
    
    def ChangeTimeFrame(self):
        """This funcion is called whenever the user gives a new time index, 
        to jump to the new given index, once "enter" button is pressed.
        """
        
#        it reads out the text in the button and converts it to an int.
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
                
                self.m.prevpicture = np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
                self.m.prevplotmask = np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
    
    
                self.m.UpdateBckgrndPicture()
                self.button_previousframe.setEnabled(False)
                
                
            elif self.Tindex == self.reader.sizet-1:
                self.button_previousframe.setEnabled(True)
                self.m.prevpicture = self.reader.LoadOneImage(self.Tindex-1, self.FOVindex)
                self.m.prevplotmask = self.reader.LoadMask(self.Tindex-1, self.FOVindex)
                   
                self.m.currpicture = self.reader.LoadOneImage(self.Tindex, self.FOVindex)
                self.m.plotmask = self.reader.LoadMask(self.Tindex, self.FOVindex)
                  
                  
                self.m.nextpicture =  np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
                self.m.nextplotmask =  np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
                
                self.m.UpdateBckgrndPicture()
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
                
                self.m.UpdateBckgrndPicture()
            
            self.UpdateTitleSubplots()
            self.button_timeindex.clearFocus()
            self.button_timeindex.setText(str(self.Tindex)+'/'+str(self.reader.sizet-1))
            
            if self.button_showval.isChecked():
                self.m.ShowCellNumbersCurr()
                self.m.ShowCellNumbersNext()
                self.m.ShowCellNumbersPrev()
            
            if self.button_hidemask.isChecked():
                self.m.HideMask()
            self.EnableCNNButtons()
        
        else:
            self.button_timeindex.clearFocus()
            return
        

     
    def CellCorrespActivation(self):
            self.Disable(self.button_cellcorespondance)
            self.statusBar.showMessage('Doing the cell correspondance')

            if self.Tindex != 0:
                self.m.plotmask = self.reader.CellCorrespondance(self.Tindex, self.FOVindex)
                self.m.updatedata()
            else:
                self.m.plotmask = self.reader.LoadSeg(self.Tindex, self.FOVindex)
                self.m.updatedata()

            self.Enable(self.button_cellcorespondance)
            self.button_cellcorespondance.setChecked(False)
            self.statusBar.clearMessage()
        
    def SegmentBoxCheck(self):
        
        if self.button_segment.isChecked():
            
            self.Disable(self.button_segment)
            self.EnableCorrectionsButtons()
            self.m.SegmentedMask = self.reader.LoadSeg(self.Tindex, self.FOVindex)
            self.m.tempplotmask = self.m.plotmask.copy()
            self.m.plotmask = self.m.SegmentedMask.copy()
            self.m.currmask.set_data((self.m.SegmentedMask%10 + 1)*(self.m.SegmentedMask != 0))
            self.m.ax.draw_artist(self.m.currplot)
            self.m.ax.draw_artist(self.m.currmask)
            self.m.update()
            self.m.flush_events()
#            update the graph
            
            self.button_SetSegmentation.setEnabled(True)
            self.button_savesegmask.setEnabled(True)
        else:
            self.m.SegmentedMask = self.m.plotmask.copy()
            self.m.plotmask = self.m.tempplotmask.copy()
            self.m.updatedata()
            self.button_SetSegmentation.setEnabled(False)
            self.button_savesegmask.setEnabled(False)
            self.Enable(self.button_segment)
    
    def SegmentThresholdedPredMask(self):
        
        segparamvalue = int(self.button_SetSegmentation.text())
        self.m.plotmask = self.reader.Segment(segparamvalue, self.Tindex,self.FOVindex)
        self.m.currmask.set_data((self.m.plotmask%10 + 1)*(self.m.plotmask != 0))
        self.m.ax.draw_artist(self.m.currplot)
        self.m.ax.draw_artist(self.m.currmask)
        self.m.update()
        self.m.flush_events()
#        self.m.SegmentedMask = self.reader.Segment(segparamvalue, self.Tindex, self.FOVindex)
#        update the plots to display the segmentation view
      
    def ButtonSaveSegMask(self):
        """saves the segmented mask
        """
        self.reader.SaveSegMask(self.Tindex, self.FOVindex, self.m.plotmask)

    
    
        
    def ThresholdBoxCheck(self):
        """if the buttons is checked it shows the thresholded version of the 
        prediction, if it is not available it justs displays a null array.
        The buttons for the setting a threshold a value and to save it are then
        activated once this button is enabled.
        """
        if self.button_threshold.isChecked():
            self.Disable(self.button_threshold)
            self.m.ThresholdMask = self.reader.LoadThreshold(self.Tindex, self.FOVindex)
            
            self.m.currmask.set_data(self.m.ThresholdMask)
            self.m.ax.draw_artist(self.m.currplot)
            self.m.ax.draw_artist(self.m.currmask)
            self.m.update()
            self.m.flush_events()
            
            
#            update the gra
            
            self.button_SetThreshold.setEnabled(True)
            self.button_savethresholdmask.setEnabled(True)
        else:
            self.m.updatedata()
            
            self.button_SetThreshold.setEnabled(False)
            self.button_savethresholdmask.setEnabled(False)
            self.Enable(self.button_threshold)

    def ThresholdPrediction(self):
        
        thresholdvalue = float(self.button_SetThreshold.text())
        
        self.m.ThresholdMask = self.reader.ThresholdPred(thresholdvalue, self.Tindex,self.FOVindex)
        self.m.currmask.set_data(self.m.ThresholdMask)
        self.m.ax.draw_artist(self.m.currplot)
        self.m.ax.draw_artist(self.m.currmask)
        self.m.update()
        self.m.flush_events()
#        self.m.ThresholdMask = self.reader.ThresholdPred(thresholdvalue, self.Tindex, self.FOVindex)
#        update the plots to display the thresholded view
      
    def ButtonSaveThresholdMask(self):
        """saves the thresholed mask
        """
#        pass
        self.reader.SaveThresholdMask(self.Tindex, self.FOVindex, self.m.ThresholdMask)

        
    def ChangePreviousFrame(self):
        
         """This function is called when the previous frame buttons is pressed 
         and it tests if the buttons is enabled and if so it calls the
         BackwardTime() function. It should avoid the let the user do multiple 
         clicks and that the function is then called afterwards several times,
         once the frames and masks of the current time index have been loaded.
         """
        
         if self.button_previousframe.isEnabled():
            self.button_previousframe.setEnabled(False)
            
#            self.button_nextframe.disconnect()
#            self.button_nextframe.setShortcut('')

#            self.button_nextframe.setEnabled(False)
#            print(self.button_nextframe.isEnabled())
#            self.button_nextframe.setChecked(False)
#            self.Testbool = False
            self.BackwardTime()
#            self.button_nextframe.setShortcut(Qt.Key_Right)
#            self.button_nextframe.pressed.connect(self.Test)
#            self.button_nextframe.setChecked(False)
            if self.Tindex >0:
                self.button_previousframe.setEnabled(True)
#            self.button_nextframe.pressed.connect(self.Test)

#            self.button_nextframe.setChecked(False)
        
#            self.Testbool = True
         else:
#            print('jamais la dedans?')
             return
             
             
    def ChangeNextFrame(self):
        
        """This function is called when the next frame buttons is pressed 
        and it tests if the buttons is enabled and if so it calls the
        ForwardTime() function. It should avoid the let the user do multiple 
        clicks and that the function is then called afterwards several times,
        once the frames and masks of the current time index have been loaded.
        """
#        self.button_nextframe.setShortcutEnabled(False)
        if self.button_nextframe.isEnabled():
            self.button_nextframe.setEnabled(False)
            
#            self.button_nextframe.disconnect()
#            self.button_nextframe.setShortcut('')

#            self.button_nextframe.setEnabled(False)
#            print(self.button_nextframe.isEnabled())
#            self.button_nextframe.setChecked(False)
#            self.Testbool = False
            self.ForwardTime()
#            self.button_nextframe.setShortcut(Qt.Key_Right)
#            self.button_nextframe.pressed.connect(self.Test)
#            self.button_nextframe.setChecked(False)
            if self.Tindex + 1 < self.reader.sizet:
                self.button_nextframe.setEnabled(True)
#            self.button_nextframe.pressed.connect(self.Test)

#            self.button_nextframe.setChecked(False)
        
#            self.Testbool = True
        else:
            return
#            print('jamais la dedans?')
#            if QKeyEvent.key() == Qt.Key_Right:
#                QKeyEvent.ignore()

        
    def ForwardTime(self):
        
        """This function switches the frame in forward time index. And it tests
        several conditions if t == lastTimeIndex-1, because then the next frame
        button has to be disabled. It also tests if the show value of cells
        button and hidemask are active in order to hide/show the mask or to 
        show the cell values.
        """
#        print(self.Tindex)
#        the t frame is defined as the currently shown frame on the display.
#        If the button "Next time frame" is pressed, this function is called
        self.statusBar.showMessage('Loading the next frame...')
#        self.button_nextframe.setEnabled(False)
#        self.button_nextframe.disconnect()
        self.Disable(self.button_nextframe)

        print("self.Tindex",self.Tindex)
        print("self.reader.sizet",self.reader.sizet)

        if self.Tindex + 1 < self.reader.sizet - 1 :
            print('if')
            self.reader.SaveMask(self.Tindex, self.FOVindex, self.m.plotmask)
            
            self.m.prevpicture = self.m.currpicture.copy()
            self.m.prevplotmask = self.m.plotmask.copy()
            
            self.m.currpicture = self.m.nextpicture.copy()
            self.m.plotmask = self.m.nextplotmask.copy()
            
            
            self.m.nextpicture = self.reader.LoadOneImage(self.Tindex+2, self.FOVindex)
            self.m.nextplotmask = self.reader.LoadMask(self.Tindex+2, self.FOVindex)
            self.m.UpdateBckgrndPicture()

            if self.Tindex + 1 == 1:
                self.button_previousframe.setEnabled(True)
                

                    
#           
        else:
            print('else')
            self.reader.SaveMask(self.Tindex, self.FOVindex, self.m.plotmask)
        
            self.m.prevpicture = self.m.currpicture.copy()
            self.m.prevplotmask = self.m.plotmask.copy()
            self.m.currpicture = self.m.nextpicture.copy()
            self.m.plotmask = self.m.nextplotmask.copy()
            
            
            
            self.m.nextpicture = np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
            self.m.nextplotmask = np.zeros([self.reader.sizey,self.reader.sizex], dtype = np.uint16)
            self.m.UpdateBckgrndPicture()

            self.button_nextframe.setEnabled(False)

        if self.button_showval.isChecked():
            self.m.ShowCellNumbersCurr()
            self.m.ShowCellNumbersNext()
            self.m.ShowCellNumbersPrev()
            

        
        

        self.Tindex = self.Tindex+1
        self.UpdateTitleSubplots()
        
        if self.button_hidemask.isChecked():
            self.m.HideMask()

        self.Enable(self.button_nextframe)
        
#        self.button_nextframe.setChecked(False)

        self.statusBar.clearMessage()
#        if self.Tindex < self.reader.sizet - 1 :
#            self.button_nextframe.setEnabled(True)
        self.button_timeindex.setText(str(self.Tindex)+'/'+str(self.reader.sizet-1))

    
    def BackwardTime(self):
        
        """This function switches the frame in backward time index. And it 
        several conditions if t == 1, because then the button previous frame has to
        be disabled. It also tests if the show value of cells button and 
        hidemask are active in order to hide/show the mask or to show the cell
        values.
        """
#        print(self.Tindex)
#        the t frame is defined as the currently shown frame on the display.
#        If the button "Previous time frame" is pressed, this function is called
        self.statusBar.showMessage('Loading the previous frame...')
#        self.button_previousframe.setEnabled(False)
#        self.button_previousframe.disconnect()
        self.Disable(self.button_previousframe)
        if self.Tindex == 1:
            
            self.reader.SaveMask(self.Tindex, self.FOVindex, self.m.plotmask)

            self.m.nextpicture = self.m.currpicture.copy()
            self.m.nextplotmask = self.m.plotmask.copy()
            
            self.m.currpicture = self.m.prevpicture.copy()
            self.m.plotmask = self.m.prevplotmask.copy()
            
            self.m.prevpicture = np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)
            self.m.prevplotmask = np.zeros([self.reader.sizey, self.reader.sizex], dtype = np.uint16)


            self.m.UpdateBckgrndPicture()

            
            self.button_previousframe.setEnabled(False)
            
            
            
        else:
            
            
            self.reader.SaveMask(self.Tindex, self.FOVindex, self.m.plotmask)
            
            self.m.nextpicture = self.m.currpicture.copy()
            self.m.nextplotmask = self.m.plotmask.copy()
            
            self.m.currpicture = self.m.prevpicture.copy()
            self.m.plotmask = self.m.prevplotmask.copy()

            self.m.prevpicture = self.reader.LoadOneImage(self.Tindex-2, self.FOVindex)
            self.m.prevplotmask = self.reader.LoadMask(self.Tindex-2, self.FOVindex)
            
            self.m.UpdateBckgrndPicture()
            if self.Tindex-1 == self.reader.sizet-2:
                self.button_nextframe.setEnabled(True)
            
            
        if self.button_showval.isChecked():
            self.m.ShowCellNumbersCurr()
            self.m.ShowCellNumbersNext()
            self.m.ShowCellNumbersPrev()
            

        

#        self.button_previousframe.clicked.connect(self.BackwardTime)
        
        self.Tindex = self.Tindex-1
        self.UpdateTitleSubplots()

        if self.button_hidemask.isChecked():
            self.m.HideMask()
            
        self.Enable(self.button_previousframe)
        

        if self.Tindex > 0:
            self.button_previousframe.setEnabled(True)          
            
#        self.button_previousframe.setChecked(False)
        self.statusBar.clearMessage()
        self.button_timeindex.setText(str(self.Tindex)+'/' + str(self.reader.sizet-1))

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
        
        
        if self.button_drawmouse.isChecked():
            
            self.statusBar.showMessage('Drawing using the brush, right click to set a value...')
            
            self.Disable(self.button_drawmouse)
            self.m.tempmask = self.m.plotmask.copy()
            
            self.id2 = self.m.mpl_connect('button_press_event', self.m.OneClick)
            
            
            
            self.id = self.m.mpl_connect('motion_notify_event', self.m.PaintBrush)
            
            self.id3 = self.m.mpl_connect('button_release_event', self.m.ReleaseClick)

            
            pixmap = QtGui.QPixmap('./icons/brush2.png')
            cursor = QtGui.QCursor(pixmap, 1,1)
            QApplication.setOverrideCursor(cursor)
        
        elif self.button_eraser.isChecked():
            
            self.statusBar.showMessage('Erasing by setting the values to 0...')
            self.Disable(self.button_eraser)
            
            self.m.tempmask = self.m.plotmask.copy()
            
            self.m.cellval = 0
            self.id2 = self.m.mpl_connect('button_press_event', self.m.OneClick)
            self.id = self.m.mpl_connect('motion_notify_event', self.m.PaintBrush)
            
            self.id3 = self.m.mpl_connect('button_release_event', self.m.ReleaseClick)

            
            pixmap = QtGui.QPixmap('./icons/eraser.png')
            cursor = QtGui.QCursor(pixmap, 1,1)
            QApplication.setOverrideCursor(cursor)
            
        else:
            self.m.mpl_disconnect(self.id3)
            self.m.mpl_disconnect(self.id2)
            self.m.mpl_disconnect(self.id)
            QApplication.restoreOverrideCursor()
            self.Enable(self.button_drawmouse)
            self.Enable(self.button_eraser)
            
            if self.button_showval.isChecked():
                self.m.ShowCellNumbersCurr()
                self.m.ShowCellNumbersNext()
                self.m.ShowCellNumbersPrev()
            self.statusBar.clearMessage()
            
            
    def UpdateTitleSubplots(self):
        """This function updates the title of the plots according to the 
        current time index. So it called whenever a frame or a fov is changed.
        """
        if self.Tindex == 0:
            
            self.m.titlecurr.set_text('Time index {}'.format(self.Tindex))
            self.m.titleprev.set_text('No frame {}'.format(''))
            self.m.titlenext.set_text('Next time index {}'.format(self.Tindex+1))
            
            
#            self.m.ax.set_title('Time index {}'.format(self.Tindex))
#            self.m.ax2.set_title('No frame {}'.format(''))
#            self.m.ax3.set_title('Next Time index {}'.format(self.Tindex+1))
#            self.m.update()
#            self.m.flush_events()
            self.m.draw()
        elif self.Tindex == self.reader.sizet-1:
            
            self.m.titlecurr.set_text('Time index {}'.format(self.Tindex))
            self.m.titleprev.set_text('Previous time index {}'.format(self.Tindex-1))
            self.m.titlenext.set_text('No frame {}'.format(''))
            
            
            
            
#            self.m.ax.set_title('Time index {}'.format(self.Tindex))
#            self.m.ax2.set_title('Previous time index {}'.format(self.Tindex-1))
#            self.m.ax3.set_title('No frame {}'.format(''))
#            self.m.update()
#            self.m.flush_events()
            self.m.draw()
        else:
            self.m.titlecurr.set_text('Time index {}'.format(self.Tindex))
            self.m.titleprev.set_text('Previous time index {}'.format(self.Tindex-1))
            self.m.titlenext.set_text('Next time index {}'.format(self.Tindex+1))
            
            
#            self.m.ax.set_title('Time index {}'.format(self.Tindex))
#            self.m.ax2.set_title('Previous time index {}'.format(self.Tindex-1))
#            self.m.ax3.set_title('Next Time index {}'.format(self.Tindex+1))
#            self.m.update()
#            self.m.flush_events()
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
            self.statusBar.showMessage('Draw a new cell...')
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
            if self.button_showval.isChecked():
                self.m.ShowCellNumbersCurr()
                self.m.ShowCellNumbersNext()
                self.m.ShowCellNumbersPrev()
            self.statusBar.clearMessage()
            
            
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
            self.statusBar.showMessage('Adding a region to an existing cell...')
            self.m.tempmask = self.m.plotmask.copy()
            self.id = self.m.mpl_connect('button_press_event', self.m.MouseClick)           
            self.Disable(self.button_add_region) 
            
        else:
            
            self.m.mpl_disconnect(self.id)
            
#            test if the list is not empty and if the dots are not all in the same line
            if  self.m.storemouseclicks and self.TestSelectedPoints():
                
                self.m.DrawRegion(False)

            else:
                self.m.updatedata()
            self.Enable(self.button_add_region)
            
            if self.button_showval.isChecked():
                self.m.ShowCellNumbersCurr()
                self.m.ShowCellNumbersNext()
                self.m.ShowCellNumbersPrev()
                
            self.statusBar.clearMessage()
            
            
            
            
            
    def Enable(self, button):
        
         """
         this functions turns on buttons all the buttons, depending on the time
         index. (next and previous buttons should not be turned on if t = 0 
         or t = lasttimeindex)
         """
         if self.button_segment.isChecked():
             self.EnableCorrectionsButtons()
             self.button_home.setEnabled(True)
             self.button_zoom.setEnabled(True)
             self.button_pan.setEnabled(True)
             self.button_back.setEnabled(True)
             self.button_forward.setEnabled(True)
         else:
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
         flag = False
         if button == self.button_add_region or button == self.button_newcell or button == self.button_exval or button == self.button_changecellvalue or button == self.button_drawmouse or button == self.button_eraser:
             if self.button_segment.isChecked():
                 flag = True

         
         for k in range(0,len(self.buttonlist)):
             if button != self.buttonlist[k]:
                 self.buttonlist[k].setEnabled(False)
         if flag:
             self.button_segment.setEnabled(True)
        
         if button == self.button_segment or button == self.button_threshold:
             self.button_home.setEnabled(True)
             self.button_zoom.setEnabled(True)
             self.button_pan.setEnabled(True)
             self.button_back.setEnabled(True)
             self.button_forward.setEnabled(True)

    def EnableCNNButtons(self):
        
        if self.reader.TestPredExisting(self.Tindex, self.FOVindex):
#            self.button_cnn.setEnabled(False)
            self.button_threshold.setEnabled(True)
            self.button_segment.setEnabled(True)
            self.button_cellcorespondance.setEnabled(True)
            self.button_extractfluorescence.setEnabled(True)
        else:
#            self.button_cnn.setEnabled(True)
            self.button_threshold.setEnabled(False)
            self.button_segment.setEnabled(False)
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
    
    def ButtonSaveMask(self):
        """
        When this function is called, it saves the current mask
        (self.m.plotmask)
        """
        
        self.reader.SaveMask(self.Tindex, self.FOVindex, self.m.plotmask)
        
    

class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None):
        """this class defines the canvas. It initializes a figure, which is then
        used to plot our data using imshow.
        
        """
        

#       define three subplots corresponding to the previous, current and next
#       time index.
        fig, (self.ax2, self.ax, self.ax3) = plt.subplots(1,3, sharex = True, sharey = True)
        
        # self.ax2.axis('tight')
        # self.ax.axis('tight')
        # self.ax3.axis('tight')
        
        # plt.gca().xaxis.set_major_locator(plt.NullLocator())
        # plt.gca().yaxis.set_major_locator(plt.NullLocator())
        fig.subplots_adjust(bottom=0, top=1, left=0, right=1, wspace = 0.05, hspace = 0.05)
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        
#       this is some mambo jambo.
        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
#       the self.currpicture attribute takes the original data and will then 
#       contain the updates drawn by the user.
        
        self.currpicture = parent.currentframe
        
        self.prevpicture = parent.previousframe
        
        self.nextpicture = parent.nextframe
        
        self.plotmask = parent.mask_curr
        
        self.prevplotmask = parent.mask_previous
        
        self.nextplotmask = parent.mask_next
            
        self.tempmask = self.plotmask.copy()
        
        self.tempplotmask = self.plotmask.copy()
        
        self.ThresholdMask = np.zeros([parent.reader.sizey, parent.reader.sizex], dtype = np.uint16)
        self.SegmentedMask = np.zeros([parent.reader.sizey, parent.reader.sizex], dtype = np.uint16)
        
#        this line is just here to not attribute a zero value to the plot
#        because if so, then it does not update the plot and it stays blank.
#        (it is unclear why..if someone finds a better solution)
        self.prevpicture = self.currpicture.copy()
        
        
        self.currplot, self.currmask = self.plot(self.currpicture, self.plotmask, self.ax)
        
        self.previousplot, self.previousmask = self.plot(self.prevpicture, self.prevplotmask, self.ax2)
        self.prevpicture = np.zeros([parent.reader.sizey, parent.reader.sizex], dtype = np.uint16)
        self.prevplotmask = np.zeros([parent.reader.sizey, parent.reader.sizex], dtype =np.uint16)

#        print('set visible')
#        self.ax2.set_visible(False)
        
        self.nextplot, self.nextmask = self.plot(self.nextpicture, self.nextplotmask, self.ax3)
        
        self.previousplot.set_data(self.prevpicture)
        self.previousmask.set_data((self.prevplotmask%10+1)*(self.prevplotmask != 0))

        self.ax2.draw_artist(self.previousplot)
        self.ax2.draw_artist(self.previousmask)
        self.update()
        self.flush_events()
        
        
        self.titlecurr = self.ax.set_title('Time index {}'.format(parent.Tindex))
        self.titleprev = self.ax2.set_title('No frame {}'.format(''))
        self.titlenext = self.ax3.set_title('Next time index {}'.format(parent.Tindex+1))
        
        
#        these variables are just set to test the states of the buttons
#        (button turned on or  off, etc..) of the buttons in the methods 
#        used in this class.
        self.button_showval_check = parent.button_showval
        self.button_newcell_check = parent.button_newcell
        self.button_add_region_check = parent.button_add_region
        self.button_drawmouse_check = parent.button_drawmouse
        self.button_eraser_check = parent.button_eraser
        self.button_hidemask_check = parent.button_hidemask
        
        
#       It will plot for the first time and return the imshow function
        
        self.currmask.set_clim(0, 10)
        self.previousmask.set_clim(0,10)
        self.nextmask.set_clim(0,10)
        
#       This attribute is a list which stores all the clicks of the mouse.
        self.storemouseclicks = []
        
#        This attribute is used to store the square where the mouse has been
#        in order than to draw lines (Paintbrush function)
        self.storebrushclicks = [[False,False]]
        
#        self.cellval is the variable which sets the value to the pixel
#        whenever something is drawn.
        self.cellval = 0
#        self.store_values = []
        
#        These are the codes used to create a polygon in the new cell/addregion
#        functions, which should be fed into the Path function
        self.codes_drawoneline = [Path.MOVETO, Path.LINETO]
        
#        These are lists storing all the annotations which are used to
#        show the values of the cells on the plots.
        self.ann_list = []
        self.ann_list_prev = []
        self.ann_list_next = []
        
        


        
    def ExchangeCellValue(self, val1, val2):
        """Swaps the values of the cell between two clusters each representing
        one cell. This method is called after the user has entered 
        values in the ExchangeCellValues window.
        """
        
        
        if (val1 in self.plotmask) and (val2 in self.plotmask):
            indices = np.where(self.plotmask == val1)
            self.plotmask[self.plotmask == val2] = val1
            for i in range(0,len(indices[0])):
                self.plotmask[indices[0][i], indices[1][i]] = val2
            self.updatedata()
        
        else:
#            print('No cell values found corresponding to the entered value')
            return
        
    def ReleaseClick(self, event):
        """This method is called from the brush button when the mouse is 
        released such that the last coordinate saved when something is drawn
        is set to zero. Because otherwise, if the user starts drawing somewhere
        else, than a straight line is draw between the last point of the
        previous mouse drawing/dragging and the new one which then starts.
        """
        if self.ax == event.inaxes:
            self.storebrushclicks[0] = [False, False]
        
    def OneClick(self, event):
        """This method is called when the Brush button is activated. And
        sets the value of self.cellval if the click is a right click, or draws
        a square if the click is a left click. (so if the user does just left
        click but does not drag, there will be only a square which is drawn )
        """
        if event.button == 3 and (event.xdata != None and event.ydata != None) and (not self.button_eraser_check.isChecked()) and self.ax == event.inaxes:
            tempx = int(event.xdata)
            tempy = int(event.ydata)
            self.cellval = self.plotmask[tempy, tempx]
            self.storebrushclicks[0] = [False, False]
            
        elif event.button == 1 and (event.xdata != None and event.ydata != None) and self.ax == event.inaxes:
            tempx = int(event.xdata)
            tempy = int(event.ydata)
            self.plotmask[tempy:tempy+3, tempx:tempx+3] = self.cellval
            self.storebrushclicks[0] = [tempx,tempy]
            
            self.updatedata()
            
        else:
            return
            
    
    def PaintBrush(self, event):
        """PantBrush is the method to paint using a "brush" and it is based
        on the mouse event in matplotlib "motion notify event". However it can 
        not record every pixel that the mouse has hovered over (it is too fast).
        So, in order to not only draw points (happens when the mouse is dragged
        too quickly), these points are interpolated here with lines.
        """
        
        if event.button == 1 and (event.xdata != None and event.ydata != None) and self.ax == event.inaxes:
        
            newx = int(event.xdata)
            newy = int(event.ydata)
#            when a new cell value is set, there is no point to interpolate, to
#            draw a line between the points. 
            if self.storebrushclicks[0][0] == False :
                self.plotmask[newy:newy+3,newx:newx+3] = self.cellval
                self.storebrushclicks[0] = [newx,newy]
            else:
                oldx = self.storebrushclicks[0][0]
                oldy = self.storebrushclicks[0][1]
                
                if newx != oldx:
                    
                    slope = (oldy-newy)/(oldx-newx)
                    offset = (newy*oldx-newx*oldy)/(oldx-newx)
                    
                    if newx > oldx:
                        for xtemp in range(oldx+1, newx+1):
                            ytemp = int(slope*xtemp + offset)
                            self.plotmask[ytemp:ytemp + 3, xtemp:xtemp+3] = self.cellval
                    else:
                        for xtemp in range(oldx-1,newx-1,-1):
                            ytemp = int(slope*xtemp + offset)
                            self.plotmask[ytemp:ytemp+3, xtemp:xtemp+3] = self.cellval
                else:
                    if newy > oldy:
                        for ytemp in range(oldy+1,newy+1):
                            self.plotmask[ytemp:ytemp+3, newx:newx+3] = self.cellval
                    else:
                        for ytemp in range(oldy-1,newy-1,-1):
                            self.plotmask[ytemp:ytemp+3, newx:newx+3] = self.cellval

            self.storebrushclicks[0][0] = newx
            self.storebrushclicks[0][1] = newy
            
            self.updatedata()
            
            
    
    def MouseClick(self,event):
        """This function is called whenever, the add region or the new cell
        buttons are active and the user clicks on the plot. For each 
        click on the plot, it records the coordinate of the click and stores
        it. When the user deactivate the new cell or add region button, 
        all the coordinates are given to the DrawRegion function (if they 
        do not all lie on the same line) and out of the coordinates, it makes
        a polygon. And then draws inside of this polygon by setting the pixels
        to the self.cellval value.
        """
#        button == 1 corresponds to the left click. 
        
        if event.button == 1 and (event.xdata != None and event.ydata != None) and self.ax == event.inaxes:
            
#           extract the coordinate of the click inside of the matplotlib figure
#           and then takes the integer part
            
            newx = int(event.xdata)
            newy = int(event.ydata)
            
#            print(newx,newy)m
#                stores the coordinates of the click
       
            self.storemouseclicks.append([newx, newy])
#                draws in the figure a small square (4x4 pixels) to
#                visualize where the user has clicked
            self.updateplot(newx, newy)
                

    def DefineColormap(self, Ncolors):
       """Define a new colormap by assigning 10 values of the jet colormap
        such that there are only colors for the values 0-10 and the values >10
        will be treated with a modulo operation (updatedata function)
       """
       jet = cm.get_cmap('jet', Ncolors)
       colors = []
       for i in range(0,Ncolors):
           if i==0 : 
#               set background transparency to 0
               temp = list(jet(i))
               temp[3]= 0.0
               colors.append(tuple(temp))
           else:
               colors.append(jet(i))
       colormap = ListedColormap(colors)
       return colormap
               
    def plot(self, picture, mask, ax):
       """this function is called for the first time when all the subplots
       are drawn.
       """
        
#       Define a new colormap with 20 colors.
       newcmp = self.DefineColormap(21)
       ax.axis("off")

       self.draw()
       return ax.imshow(picture, interpolation= 'None', origin = 'upper', cmap = 'gray_r'), ax.imshow((mask%10+1)*(mask != 0), origin = 'upper', interpolation = 'None', alpha = 0.2, cmap = newcmp)
   
    
    def UpdateBckgrndPicture(self):
        """this function can be called to redraw all the pictures and the mask,
        so it is called whenever a time index is entered by the user and
        the corresponding pictures and masks are updated. And then they are
        drawn here. 
        When the user changes time frame using the next or previous time frame
        buttons, it is also this function which is called.
        When the user changes the field of view, it is also
        this function which finally draws all the plots.

        """
        
        self.currplot.set_data(self.currpicture)
        self.currplot.set_clim(np.amin(self.currpicture), np.amax(self.currpicture))
        self.currmask.set_data((self.plotmask%10+1)*(self.plotmask!=0))
        self.ax.draw_artist(self.currplot)
        self.ax.draw_artist(self.currmask)
        

        self.previousplot.set_data(self.prevpicture)
        self.previousplot.set_clim(np.amin(self.prevpicture), np.amax(self.prevpicture))
        self.previousmask.set_data((self.prevplotmask%10+1)*(self.prevplotmask != 0))

        
        self.ax2.draw_artist(self.previousplot)
        self.ax2.draw_artist(self.previousmask)
        
        self.nextplot.set_data(self.nextpicture)
        self.nextplot.set_clim(np.amin(self.nextpicture), np.amax(self.nextpicture))
        self.nextmask.set_data((self.nextplotmask % 10 +1 )*(self.nextplotmask != 0))
        self.ax3.draw_artist(self.nextplot)
        self.ax3.draw_artist(self.nextmask)
        
        
        self.update()
        self.flush_events()
        
        
    def updatedata(self, flag = True):


       """
       In order to just display the cells so regions with value > 0
       and also to assign to each of the cell values one color,
       the modulo 10 of the value is take and we add 1, to distinguish
       the values of 10,20,30,... from the background (although the bckgrnd
       gets with the addition the value 1) and the result of the 
       modulo is multiplied with a matrix containing a False value for the 
       background coordinates, setting the background to 0 again.
       """
       if flag:
#           print("plotmask",self.plotmask.shape)
           self.currmask.set_data((self.plotmask%10+1)*(self.plotmask!=0))
       else :
           self.currmask.set_data((self.tempmask%10+1)*(self.tempmask!=0))
       
       
       
#       show the updates by redrawing the array using draw_artist, it is faster 
#       to use as it only redraws the array itself, and not everything else.
       
       self.ax.draw_artist(self.currplot)
       self.ax.draw_artist(self.currmask)
#       self.ax.text(500,500,'test')
       self.update()
       self.flush_events()
#       
#       if self.button_showval_check.isChecked():
#           self.ShowCellNumbersCurr()
#           self.ShowCellNumbersNext()
#           self.ShowCellNumbersPrev()
       
    def Update3Plots(self):
        """This function is just used to draw the update the masks on
        the three subplots. It is only used by the Hidemask function. 
        To "show" the masks again when the button is unchecked.
        """
        
#        self.currmask.set_data((self.plotmask%10+1)*(self.plotmask!=0))
        self.ax.draw_artist(self.currplot)
        self.ax.draw_artist(self.currmask)
        
        self.ax2.draw_artist(self.previousplot)
        self.ax2.draw_artist(self.previousmask)
        
        self.ax3.draw_artist(self.nextplot)
        self.ax3.draw_artist(self.nextmask)
        
        self.update()
        self.flush_events()
       
    def HideMask(self):
        
        if self.button_hidemask_check.isChecked():
            self.ax.draw_artist(self.currplot)
            self.ax2.draw_artist(self.previousplot)
            self.ax3.draw_artist(self.nextplot)
            self.update()
            self.flush_events()
            
        else:
            self.Update3Plots()
        
       
    def ShowCellNumbersCurr(self):
         """This function is called to display the cell values and it 
         takes 10 random points inside of the cell, computes the mean of these
         points and this gives the coordinate where the number will be 
         displayed. The number to be displayed is just given by the value
         in the mask of the cell.
         This function is just used for the current time subplot.
         """
         
         
         for i,a in enumerate(self.ann_list):
                 a.remove()
         self.ann_list[:] = []
         

         if self.button_showval_check.isChecked():
             vals = np.unique(self.plotmask)
             vals = np.delete(vals,np.where(vals==0)) #SJR: for some reason are floats and contains background (0)
             xtemp = []
             ytemp = []
             val = []
             for k in vals:
                 y,x = (self.plotmask==k).nonzero() # this was wrong x,y I believe
                 sample = np.random.choice(len(x), size=20, replace=True)
                 meanx = np.mean(x[sample])
                 meany = np.mean(y[sample])
                 xtemp.append(int(round(meanx)))
                 ytemp.append(int(round(meany)))
                 val.append(k)
         
##         if self.button_showval_check.isChecked():
##                          
##             maxval = np.amax(self.plotmask)
##             minval =  1
##             xtemp = []
##             ytemp = []
##             val =[]
##             for k in range(minval,maxval + 1):
##                 if k in self.plotmask:
##                     indices = np.where(self.plotmask == k)
##                     sampley = random.choices(list(indices[0]), k = 10)
##                     samplex = random.choices(list(indices[1]), k = 10)
##                     meanx = np.mean(samplex)
##                     meany = np.mean(sampley)
##                     xtemp.append(int(round(meanx)))
##                     ytemp.append(int(round(meany)))
##                     val.append(k)
             if xtemp:
                 for i in range(0,len(xtemp)):
                      ann = self.ax.annotate(str(int(val[i])), (xtemp[i], ytemp[i]))
                      self.ann_list.append(ann)
             
            
             self.draw()
#             val, ct = np.unique(self.plotmask, return_counts = True)
#             print(val)
#             print(ct)
             
         else:
             
             for i,a in enumerate(self.ann_list):
                 a.remove()
             self.ann_list[:] = []
             
#             self.txt.remove()
             self.updatedata()
             
    def ShowCellNumbersPrev(self):
         """This function is called to display the cell values and it 
         takes 10 random points inside of the cell, computes the mean of these
         points and this gives the coordinate where the number will be 
         displayed. The number to be displayed is just given by the value
         in the mask of the cell.
         This function is just used for the previous time subplot.
         """
         
         for i,a in enumerate(self.ann_list_prev):
                 a.remove()
         self.ann_list_prev[:] = []
         
         
         if self.button_showval_check.isChecked():
                          
             maxval = int(np.amax(self.prevplotmask))
             minval =  1
             xtemp = []
             ytemp = []
             val = []
             
             for k in range(minval,maxval + 1):
                 if k in self.prevplotmask:
                     indices = np.where(self.prevplotmask == k)
                     sampley = random.choices(list(indices[0]), k = 10)
                     samplex = random.choices(list(indices[1]), k = 10)
                     meanx = np.mean(samplex)
                     meany = np.mean(sampley)
                     xtemp.append(int(round(meanx)))
                     ytemp.append(int(round(meany)))
                     val.append(k)
             if xtemp:
                 for i in range(0,len(xtemp)):
                      ann = self.ax2.annotate(str(val[i]), (xtemp[i], ytemp[i]))
                      self.ann_list_prev.append(ann)
             
             self.draw()
             
         else:
             
             for i,a in enumerate(self.ann_list_prev):
                 a.remove()
             self.ann_list_prev[:] = []
             

             self.previousmask.set_data((self.prevplotmask%10+1)*(self.prevplotmask!=0))

             self.ax2.draw_artist(self.previousplot)
             self.ax2.draw_artist(self.previousmask)
             self.update()
             self.flush_events()
             
             
    def ShowCellNumbersNext(self):
        
         """This function is called to display the cell values and it 
         takes 10 random points inside of the cell, computes the mean of these
         points and this gives the coordinate where the number will be 
         displayed. The number to be displayed is just given by the value
         in the mask of the cell.
         This function is just used for the next time subplot.
         """
        
         for i,a in enumerate(self.ann_list_next):
                 a.remove()
         self.ann_list_next[:] = []
             
        
        
        
         if self.button_showval_check.isChecked():
                          
             maxval = int(np.amax(self.nextplotmask))
             minval =  1
             xtemp = []
             ytemp = []
             val = []
             for k in range(minval,maxval + 1):
                 if k in self.nextplotmask:
                     indices = np.where(self.nextplotmask == k)
                     sampley = random.choices(list(indices[0]), k = 10)
                     samplex = random.choices(list(indices[1]), k = 10)
                     meanx = np.mean(samplex)
                     meany = np.mean(sampley)
                     xtemp.append(int(round(meanx)))
                     ytemp.append(int(round(meany)))
                     val.append(k)
             if xtemp:
                 for i in range(0,len(xtemp)):
                      ann = self.ax3.annotate(str(val[i]), (xtemp[i], ytemp[i]))
                      self.ann_list_next.append(ann)
             
             self.draw()
             
         else:
             
             for i,a in enumerate(self.ann_list_next):
                 a.remove()
             self.ann_list_next[:] = []
             

             self.nextmask.set_data((self.nextplotmask%10+1)*(self.nextplotmask!=0))

             self.ax3.draw_artist(self.nextplot)
             self.ax3.draw_artist(self.nextmask)
             self.update()
             self.flush_events()
            
        
        
    def updateplot(self, posx, posy):
        
        
        
        
# it updates the plot once the user clicks on the plot and draws a 4x4 pixel dot
# at the coordinate of the click 
#          self.modulomask = self.plotmask.copy()
          xtemp, ytemp = self.storemouseclicks[0]
#         remove the first coordinate as it should only coorespond 
#         to the value that the user wants to attribute to the drawn region   

#          here we initialize the value attributed to the pixels.
#          it means that the first click selects the value that will be attributed to
#          the pixels inside the polygon (drawn by the following mouse clicks of the user)
          
          self.cellval = self.plotmask[ytemp, xtemp]
          
          

          
#          drawing the 2x2 square ot of the mouse click
          
          
          if (self.button_newcell_check.isChecked() or self.button_drawmouse_check.isChecked()) and self.cellval == 0:
              self.tempmask[posy:posy+2, posx:posx+2] = 9
          else:
              self.tempmask[posy:posy+2,posx:posx+2] = self.cellval

#          plot the mouseclick
         
          self.updatedata(False)
          

          
    def DrawRegion(self, flag):
        """
        this method is used to draw either a new cell (flag = true) or to add a region to 
        an existing cell (flag = false). The flag will just be used to set the
        value of pixels (= self.cellval) in the drawn region. 
        If flag = true, then the value will be the maximal value plus 1. Such 
        that it attributes a new value to the new cell.
        If flag = false, then it will use the value of the first click to set
        the value of the pixels in the new added region. 
        """

        
        
#        here the values that have been changed to mark the mouse clicks are 
#        restored such that they don't appear when the region/new cell is 
#        drawn.


        
        if flag:
#            if new cell is added, it sets the value of the drawn pixels to a new value
#            corresponding to the new cell
            self.cellval = np.amax(self.plotmask) + 1
        else:
#            The first value is taken out as it is just used to set the value
#            to the new region.
#            self.store_values.pop(0)
            self.storemouseclicks.pop(0)
                
        
        if len(self.storemouseclicks) <= 2:
#            if only two points or less have been click, it cannot make a area
#            so it justs discards these values and returns. 
            self.storemouseclicks = list(self.storemouseclicks)

            self.storemouseclicks.clear()

            self.updatedata(True)
#            self.store_values.clear()
            return
        
        else:
#            add the first point because to use the path function, one has to close 
#            the path by returning to the initial point.
            self.storemouseclicks.append(self.storemouseclicks[0])

#            codes are requested by the path function in order to make a polygon
#            out of the points that have been selected.
            
            codes = np.zeros(len(self.storemouseclicks))
            codes[0] = Path.MOVETO
            codes[len(codes)-1]= Path.CLOSEPOLY
            codes[1:len(codes)-1] = Path.LINETO
            codes = list(codes)
            
#            out of the coordinates of the mouse clicks and of the code, it makes
#            a path/contour which corresponds to the added region/new cell.
            path = Path(self.storemouseclicks, codes)
            
            
                
            self.storemouseclicks = np.array(self.storemouseclicks)
          
#          Take a square around the drawn region, where the drawn region fits inside.
            minx = min(self.storemouseclicks[:,0])
            maxx = max(self.storemouseclicks[:,0])
          
            miny = min(self.storemouseclicks[:,1])
            maxy= max(self.storemouseclicks[:,1])
          
#            creates arrays of coordinates of the whole square surrounding
#            the drawn region
            array_x = np.arange(minx, maxx, 1)
            array_y = np.arange(miny, maxy, 1)
#            
            array_coord = []
#          takes all the coordinates to couple them and store them in array_coord
            for xi in range(0,len(array_x)):
               for yi in range(0,len(array_y)):
                  
                  array_coord.append((array_x[xi], array_y[yi]))
          
#          path_contains_points returns an array of bool values
#          where for each coordinates it tests if it is inside the path
                  
            pix_inside_path = path.contains_points(array_coord)

#            for each coordinate where the contains_points method returned true
#            the value of the self.currpicture matrix is changed, it draws the region
#            defined by the user
            
            for j in range(0,len(pix_inside_path)):
              if pix_inside_path[j]:
                  x,y = array_coord[j]
                  self.plotmask[y,x]= self.cellval

            
#           once the self.currpicture has been updated it is drawn by callinf the
#           updatedata method.
            
            self.updatedata()

            
        self.storemouseclicks = list(self.storemouseclicks)

#       empty the lists ready for the next region to be drawn.
        self.storemouseclicks.clear()
#        self.store_values.clear()  
        


if __name__ == '__main__':
    app = QApplication(sys.argv)
    wind = dfb.FileBrowser()
    if wind.exec_():
        nd2name1 = wind.nd2name
        hdfname1 = wind.hdfname
        hdfnewname = wind.newhdfentry.text()
        ex = App(nd2name1, hdfname1, hdfnewname)
        sys.exit(app.exec_())
    else:
        app.exit()
        
