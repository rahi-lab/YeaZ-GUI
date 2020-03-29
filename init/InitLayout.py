# -*- coding: utf-8 -*-
"""
Initializing the layout of the main window. It places the buttons and the 
pictures at the desired positions.
"""
#from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget, QPushButton, QShortcut, QComboBox, QCheckBox, QLineEdit, QMenu, QAction, QStatusBar
#from PyQt5 import QtGui
#from PyQt5.QtCore import pyqtSignal, QObject, Qt
from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5


def Init(parent):
    
#        LAYOUT OF THE MAIN WINDOW
        layout = QtWidgets.QVBoxLayout(parent._main)
        
        
#        LAYOUT FOR THE THRESHOLD BUTTONS
#        all the buttons of the threshold function are placed in an horizontal 
#        stack
        hbox_threshold = QtWidgets.QHBoxLayout()
        hbox_threshold.addWidget(parent.button_threshold)
        hbox_threshold.addWidget(parent.button_SetThreshold)
        hbox_threshold.addWidget(parent.button_savethresholdmask)
#        if this line is not put, then the buttons are placed along the whole
#        length of the window, in this way they are all grouped to the left.
        hbox_threshold.addStretch(1)       
      
        
        
#        LAYOUT FOR THE SEGMENTATION BUTTONS
#        all the buttons of the segment function are placed in an 
#        horizontal stack        
        hbox_segment = QtWidgets.QHBoxLayout()
        hbox_segment.addWidget(parent.button_segment)
        hbox_segment.addWidget(parent.button_SetSegmentation)
        hbox_segment.addWidget(parent.button_savesegmask)
#        if this line is not put, then the buttons are placed along the whole
#        length of the window, in this way they are all grouped to the left.
        hbox_segment.addStretch(1)    
        
        
#        LAYOUT FOR THE TOOLBAR BUTTONS
#        all the buttons of the toolbar are placed in an 
#        horizontal stack   
        hbox = QtWidgets.QHBoxLayout()
        
        hbox.addWidget(parent.button_home) 
        hbox.addWidget(parent.button_back)
        hbox.addWidget(parent.button_forward)
        hbox.addWidget(parent.button_pan)
        hbox.addWidget(parent.button_zoom)
        
        hbox.addStretch(1)
#       we add all our widgets in the layout 
        layout.addLayout(hbox)
#        layout.addWidget(parent.button_zoom)
#        layout.addWidget
        
        
#        makes a horizontal layout for the buttons used to navigate through 
#        the time axis.
        hboxtimeframes = QtWidgets.QHBoxLayout()
        hboxtimeframes.addWidget(parent.button_previousframe)
        hboxtimeframes.addWidget(parent.button_timeindex)
        hboxtimeframes.addWidget(parent.button_nextframe)
        layout.addWidget(parent.m)
        
        layout.addLayout(hboxtimeframes)
        
#        layout.addStretch(0.7)
        
        hboxcorrectionsbuttons = QtWidgets.QHBoxLayout()
        hboxcorrectionsbuttons.addWidget(parent.button_add_region)
        hboxcorrectionsbuttons.addWidget(parent.button_newcell)

        hboxcorrectionsbuttons.addWidget(parent.button_drawmouse)
        hboxcorrectionsbuttons.addWidget(parent.button_eraser)
        hboxcorrectionsbuttons.addWidget(parent.button_savemask)
        hboxcorrectionsbuttons.addStretch(1)
        layout.addLayout(hboxcorrectionsbuttons)
                
#        layout.addStretch(0.7)
        hboxcellval = QtWidgets.QHBoxLayout()
        hboxcellval.addWidget(parent.button_exval)
        hboxcellval.addWidget(parent.button_changecellvalue)
        hboxcellval.addStretch(1)
        layout.addLayout(hboxcellval)


        hboxlistbuttons = QtWidgets.QHBoxLayout()
        hboxlistbuttons.addWidget(parent.button_fov)
        hboxlistbuttons.addWidget(parent.button_channel)
        hboxlistbuttons.addStretch(1)
        layout.addLayout(hboxlistbuttons)

        layout.addWidget(parent.button_extractfluorescence)
        
        hboxcheckbox = QtWidgets.QHBoxLayout()
        hboxcheckbox.addWidget(parent.button_showval)
        hboxcheckbox.addWidget(parent.button_hidemask)
        hboxcheckbox.addStretch(1)

        layout.addLayout(hboxcheckbox)
        
        
        layout.addWidget(parent.button_cnn)
        
        layout.addLayout(hbox_threshold)
        
        layout.addLayout(hbox_segment)
        layout.addWidget(parent.button_cellcorespondance)


