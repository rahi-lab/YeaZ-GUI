# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 17:38:58 2019
"""

from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QLineEdit, QFormLayout, 
                             QLabel, QListWidget, QAbstractItemView, QCheckBox,
                             QButtonGroup, QRadioButton, QComboBox)
from PyQt6 import QtGui


class CustomDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super(CustomDialog, self).__init__(*args, **kwargs)
        
        app, = args
        maxtimeindex = app.reader.sizet
        
        self.setWindowTitle("Launch NN")
        self.setGeometry(100,100, 500,200)
        
        self.entry1 = QLineEdit()
        self.entry1.setValidator(QtGui.QIntValidator(0,int(maxtimeindex-1)))
        self.entry2 = QLineEdit()
        self.entry2.setValidator(QtGui.QIntValidator(0,int(maxtimeindex-1)))
        
        # FOV dialog
        self.listfov = QListWidget()
        self.listfov.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for f in range(0, app.reader.Npos):
            self.listfov.addItem('Field of View {}'.format(f+1))

        self.labeltime = QLabel("Enter range of frames ({}-{}) to segment".format(0, app.reader.sizet-1))
        
        self.entry_threshold = QLineEdit()
        self.entry_threshold.setValidator(QtGui.QDoubleValidator())
        self.entry_threshold.setText('0.5')
        
        self.entry_segmentation = QLineEdit()
        self.entry_segmentation.setValidator(QtGui.QIntValidator())
        self.entry_segmentation.setText('5')
                
        flo = QFormLayout()
        flo.addWidget(self.labeltime)
        flo.addRow('Start from frame:', self.entry1)
        flo.addRow('End at frame:', self.entry2)        
        flo.addRow('Select field(s) of view:', self.listfov)
        flo.addRow('Threshold value:', self.entry_threshold)
        flo.addRow('Min. distance between seeds:', self.entry_segmentation)
        
        self.mic_type = QComboBox()
        self.mic_type.addItem("Image type", None)
        self.mic_type.addItem("Bright-field budding yeast", "bf")
        self.mic_type.addItem("Phase contrast budding yeast", "pc")
        self.mic_type.addItem("Bud phase contrast fission", "fission")

        self.mic_type.setCurrentIndex(0)
        flo.addRow("Select image type: ", self.mic_type)
        
        
        self.device_selection = QComboBox()
        self.device_selection.addItem("CPU", "cpu")
        self.device_selection.addItem("GPU", "cuda")
        self.device_selection.setCurrentIndex(0)
        flo.addRow("Select device for running neural network: ", self.device_selection)
        
        QBtn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        flo.addWidget(self.buttonBox)
        self.setLayout(flo)
        

        
