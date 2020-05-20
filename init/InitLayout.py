# -*- coding: utf-8 -*-
"""
Initializing the layout of the main window. It places the buttons and the 
pictures at the desired positions.
"""
from matplotlib.backends.qt_compat import QtWidgets


def Init(parent):

    
    # LAYOUT OF THE MAIN WINDOW
    layout = QtWidgets.QVBoxLayout(parent._main)
    
    # LAYOUT FOR THE TOOLBAR BUTTONS
    hbox = QtWidgets.QHBoxLayout()
    hbox.addWidget(parent.button_home) 
    hbox.addWidget(parent.button_back)
    hbox.addWidget(parent.button_forward)
    hbox.addWidget(parent.button_pan)
    hbox.addWidget(parent.button_zoom)
    hbox.addStretch(1)
    layout.addLayout(hbox)
    
    # TIME NAVIGATION
    hboxtimeframes = QtWidgets.QHBoxLayout()
    hboxtimeframes.addWidget(parent.button_fov)
    hboxtimeframes.addWidget(parent.button_channel)
    hboxtimeframes.addStretch()
    hboxtimeframes.addWidget(parent.button_previousframe)
    hboxtimeframes.addWidget(parent.button_timeindex)
    hboxtimeframes.addWidget(parent.button_nextframe)
    hboxtimeframes.addStretch()
    
    # IMAGE DISPLAY
    hlayout = QtWidgets.QHBoxLayout()
    hlayout.addWidget(parent.m)
    hlayout.setContentsMargins(0, 0, 0, 0)
    layout.addLayout(hlayout)        
    layout.addLayout(hboxtimeframes)
    
    # CORRECTIONS/ IMAGE EDITS       
    hboxcorrectionsbuttons = QtWidgets.QHBoxLayout()
    hboxcorrectionsbuttons.addWidget(parent.button_add_region)
    hboxcorrectionsbuttons.addWidget(parent.button_newcell)
    hboxcorrectionsbuttons.addWidget(parent.button_drawmouse)
    hboxcorrectionsbuttons.addWidget(parent.button_eraser)
    hboxcorrectionsbuttons.addWidget(parent.label_brushsize)
    hboxcorrectionsbuttons.addWidget(parent.spinbox_brushsize)
    hboxcorrectionsbuttons.addStretch(2)
    hboxcorrectionsbuttons.addWidget(parent.button_showval)
    hboxcorrectionsbuttons.addWidget(parent.button_hidemask)
    layout.addLayout(hboxcorrectionsbuttons)
    
    # LAYOUT FOR EDITING CELL VALUES, SHOW CELL VALUES AND HIDE MASK, CNN BUTTONS
    hboxcellval = QtWidgets.QHBoxLayout()
    hboxcellval.addWidget(parent.button_exval)
    hboxcellval.addWidget(parent.button_changecellvalue)
    hboxcellval.addWidget(parent.button_cellcorespondance)
    hboxcellval.addStretch(1)
    hboxcellval.addWidget(parent.button_cnn)
    hboxcellval.addWidget(parent.button_extractfluorescence)
    layout.addLayout(hboxcellval)

