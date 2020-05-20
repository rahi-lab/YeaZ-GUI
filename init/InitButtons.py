# -*- coding: utf-8 -*-
"""
Initializing all the buttons in this file.
"""
from PyQt5.QtWidgets import QPushButton, QComboBox, QLineEdit
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
import numpy as np

def Init(parent):
    """
    configuration of all the buttons, some buttons just need to be toggled
    meaning that they need just to be clicked and the function associated 
    to the button is called and executed. Other buttons are checkable 
    meaning that until the user has not finished to use the function
    connected to the button, this button stays active (or Checked)
    """

    # hide / show cnn buttons
    parent.button_hide_show.setCheckable(True)    
    parent.button_hide_show.setMaximumWidth(150)
    parent.button_hide_show.clicked.connect(parent.ShowHideCNNbuttons)
    parent.button_hide_show.setStatusTip('Press to hide and show neural network buttons')

    # ADD REGION
    parent.button_add_region.setCheckable(True)
    parent.button_add_region.setMaximumWidth(150)
    parent.button_add_region.clicked.connect(parent.clickmethod)
    parent.button_add_region.setShortcut("R")
    parent.button_add_region.setToolTip("Use R Key for shortcut")
    parent.button_add_region.setStatusTip('The first left click sets the value for the next clicks, then draw polygons')
    
    # NEW CELL
    parent.button_newcell.setCheckable(True)
    parent.button_newcell.setMaximumWidth(150)
    parent.button_newcell.setShortcut("N")
    parent.button_newcell.setToolTip("Use N Key for shortcut")
    parent.button_newcell.clicked.connect(parent.ClickNewCell)
    parent.button_newcell.setStatusTip('Use the left click to produce a polygon with a new cell value')
    
    # NEXT FRAME (TIME AXIS)
    parent.button_nextframe.toggle()
    parent.button_nextframe.pressed.connect(parent.ChangeNextFrame)
    parent.button_nextframe.setToolTip("Use right arrow key for shortcut")
    parent.button_nextframe.setMaximumWidth(150)
    parent.button_nextframe.setShortcut(Qt.Key_Right)
    
    # if there is only one picture than this button is disabled
    if np.all(parent.nextframe == 0):
        parent.button_nextframe.setEnabled(False)    
    
    # PREVIOUS FRAME (TIME AXIS)
    parent.button_previousframe.setEnabled(False)
    parent.button_previousframe.toggle()
    parent.button_previousframe.pressed.connect(parent.ChangePreviousFrame)
    parent.button_previousframe.setToolTip("Use left arrow key for shortcut")
    parent.button_previousframe.setMaximumWidth(150)
    parent.button_previousframe.setShortcut(Qt.Key_Left)
    parent.button_previousframe.move(100,100)
        
    # ZOOM
    parent.button_zoom = QPushButton()
    parent.button_zoom.clicked.connect(parent.ZoomTlbar)
    parent.button_zoom.setIcon(QtGui.QIcon('./icons/ZoomIcon.png'))
    parent.button_zoom.setMaximumWidth(30)
    parent.button_zoom.setMaximumHeight(30)
    parent.button_zoom.setStyleSheet("QPushButton:hover { background-color: blue }" )
    parent.button_zoom.setCheckable(True)
    parent.button_zoom.setShortcut("Z")
    parent.button_zoom.setToolTip("Use Z Key for shortcut")
    parent.buttonlist.append(parent.button_zoom)
    
    # HOME
    parent.button_home = QPushButton()
    parent.button_home.clicked.connect(parent.HomeTlbar)
    parent.button_home.setIcon(QtGui.QIcon('./icons/HomeIcon.png'))
    parent.button_home.setMaximumWidth(30)
    parent.button_home.setMaximumHeight(30)
    parent.button_home.setStyleSheet("QPushButton:hover { background-color: blue }" )
    parent.button_home.setShortcut("H")
    parent.button_home.setToolTip("Use H Key for shortcut")
    parent.button_home.setStatusTip('Reset Zoom')
    parent.buttonlist.append(parent.button_home)
    
    # PREVIOUS SCALE (ZOOM SCALE)
    parent.button_back = QPushButton()
    parent.button_back.clicked.connect(parent.BackTlbar)
    parent.button_back.setIcon(QtGui.QIcon('./icons/LeftArrowIcon.png'))
    parent.button_back.setMaximumWidth(30)
    parent.button_back.setMaximumHeight(30)
    parent.button_back.setStyleSheet("QPushButton:hover { background-color: blue }" )
    parent.button_back.setStatusTip('Go back to previous zoom scale')
    parent.buttonlist.append(parent.button_back)
    
    # NEXT SCALE (ZOOM SCALE)
    parent.button_forward = QPushButton()
    parent.button_forward.clicked.connect(parent.ForwardTlbar)
    parent.button_forward.setIcon(QtGui.QIcon('./icons/RightArrowIcon.png'))
    parent.button_forward.setMaximumWidth(30)
    parent.button_forward.setMaximumHeight(30)
    parent.button_forward.setStyleSheet("QPushButton:hover { background-color: blue }")
    parent.button_back.setStatusTip('Go to next zoom scale')
    parent.buttonlist.append(parent.button_forward)
    
    # PAN 
    parent.button_pan = QPushButton()
    parent.button_pan.clicked.connect(parent.PanTlbar)
    parent.button_pan.setIcon(QtGui.QIcon('./icons/MoveArrowsIcon.png'))
    parent.button_pan.setMaximumWidth(30)
    parent.button_pan.setMaximumHeight(30)
    parent.button_pan.setStyleSheet("QPushButton:hover { background-color: blue }")
    parent.button_pan.setCheckable(True)
    parent.button_pan.setShortcut("P")
    parent.button_pan.setToolTip("Use P Key for shortcut")
    parent.button_pan.setStatusTip('Pan')
    parent.buttonlist.append(parent.button_pan)
    
    # BRUSH 
    parent.button_drawmouse.setCheckable(True)
    parent.button_drawmouse.clicked.connect(parent.MouseDraw)
    parent.button_drawmouse.setToolTip("Use B Key for shortcut")
    parent.button_drawmouse.setShortcut("B")
    parent.button_drawmouse.setMaximumWidth(150)
    parent.button_drawmouse.setStatusTip('Right click to select cell value and then left click and drag to draw')
    
    # ERASER
    parent.button_eraser.setCheckable(True)
    parent.button_eraser.clicked.connect(parent.MouseDraw)
    parent.button_eraser.setToolTip("Use E Key for shortcut")
    parent.button_eraser.setShortcut("E")
    parent.button_eraser.setMaximumWidth(150)
    parent.button_eraser.setStatusTip('Right click and drag to set values to 0')
    
    # BRUSHSIZE
    parent.spinbox_brushsize.setMinimum(1)
    parent.spinbox_brushsize.setMaximumWidth(100)
    parent.spinbox_brushsize.setValue(3)
    
    # EXCHANGE CELL VALUES
    parent.button_exval.toggle()
    parent.button_exval.setEnabled(True)
    parent.button_exval.clicked.connect(parent.DialogBoxECV)
    parent.button_exval.setMaximumWidth(150)
    parent.button_exval.setStatusTip('Exchange values between two cells')

    # CHANGE CELL VALUE
    parent.button_changecellvalue.setCheckable(True)
    parent.button_changecellvalue.setEnabled(True)
    parent.button_changecellvalue.clicked.connect(parent.ChangeOneValue)
    parent.button_changecellvalue.setMaximumWidth(150)
    parent.button_changecellvalue.setStatusTip('Change value of one cell')
    parent.button_changecellvalue.setToolTip('Use left click to select one cell and enter a new value')
                
    # MAKE THE CELL CORRESPONDANCE
    parent.button_cellcorespondance.setEnabled(False)
    parent.button_cellcorespondance.setCheckable(True)
    parent.button_cellcorespondance.clicked.connect(parent.CellCorrespActivation)
    parent.button_cellcorespondance.setMaximumWidth(150)
    parent.button_cellcorespondance.setStatusTip('Recalculate the cell correspondance to the previous time frame')
    
    # EXTRACT FLUORESCENCE IN DIFFERENT CHANNELS    
    parent.button_extractfluorescence.setEnabled(False)
    parent.button_extractfluorescence.toggle()
    parent.button_extractfluorescence.clicked.connect(parent.ButtonFluo)
    parent.button_extractfluorescence.setMaximumWidth(150)
    parent.button_extractfluorescence.setStatusTip('Extract the total intensity, area and variance of the cells in the different channels')
    
    # SHOW THE VALUES OF THE CELLS
    parent.button_showval.stateChanged.connect(parent.m.UpdatePlots)
    parent.button_showval.setShortcut('V')
    parent.button_showval.setToolTip("Use V Key for shortcut")
        
    # HIDE/SHOW THE MASK
    parent.button_hidemask.stateChanged.connect(parent.m.HideMask)    
    
    # CHANGE TIME INDEX
    parent.button_timeindex = QLineEdit()
    parent.button_timeindex.setPlaceholderText('Time index 0-{}'.format(parent.reader.sizet-1))
    parent.button_timeindex.setValidator(QtGui.QIntValidator(0,int(parent.reader.sizet-1)))
    parent.button_timeindex.returnPressed.connect(parent.ChangeTimeFrame)
    parent.button_timeindex.setMaximumWidth(150)
    parent.buttonlist.append(parent.button_timeindex)
    
    # FIELDS OF VIEW BUTTON
    parent.button_fov = QComboBox()
    list_fov = []
    for i in range(0, parent.reader.Npos):
        list_fov.append("Field of View " + str(i+1))
    parent.button_fov.addItems(list_fov)
    parent.button_fov.setMaximumWidth(150)
    parent.buttonlist.append(parent.button_fov)
    parent.button_fov.activated.connect(parent.SelectFov)
            
    # CHANGE CHANNEL BUTTON
    parent.button_channel = QComboBox()
    parent.button_channel.addItems(parent.reader.channel_names)
    parent.button_channel.setMaximumWidth(150)
    parent.buttonlist.append(parent.button_channel)
    parent.button_channel.activated.connect(parent.SelectChannel)
        
    # NEURAL NETWORK BUTTON
    parent.button_cnn.setCheckable(True)
    parent.button_cnn.pressed.connect(parent.LaunchBatchPrediction)
    parent.button_cnn.setToolTip("Launches the CNN on a range of images")
    parent.button_cnn.setMaximumWidth(150)
    parent.EnableCNNButtons()
        

