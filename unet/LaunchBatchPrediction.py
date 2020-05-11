# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 17:38:58 2019
"""

from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QLineEdit, QFormLayout, 
                             QLabel, QListWidget, QAbstractItemView, QCheckBox)
from PyQt5 import QtGui


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
        self.listfov.setSelectionMode(QAbstractItemView.MultiSelection)
        for f in range(0, app.reader.Npos):
            self.listfov.addItem('Field of View {}'.format(f+1))

        self.labeltime = QLabel("Enter range ({}-{}) for time axis".format(0, app.reader.sizet-1))
        
        self.entry_threshold = QLineEdit()
        self.entry_threshold.setValidator(QtGui.QDoubleValidator())
        self.entry_threshold.setText('0.5')
        
        self.entry_segmentation = QLineEdit()
        self.entry_segmentation.setValidator(QtGui.QIntValidator())
        self.entry_segmentation.setText('10')
        
        self.tracking_checkbox = QCheckBox()
        
        flo = QFormLayout()
        flo.addWidget(self.labeltime)
        flo.addRow('Lower Boundary for time axis', self.entry1)
        flo.addRow('Upper Boundary for time axis', self.entry2)        
        flo.addRow('Select Field(s) of fiew from  the list', self.listfov)
        flo.addRow('Enter a threshold value', self.entry_threshold)
        flo.addRow('Enter a segmentation value', self.entry_segmentation)
        flo.addRow('Apply Cell Tracker', self.tracking_checkbox)
        
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        flo.addWidget(self.buttonBox)
        self.setLayout(flo)
        

        
