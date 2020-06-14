# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 17:38:58 2019
"""

from PyQt5.QtWidgets import (QPushButton, QDialog, QDialogButtonBox, 
                             QLineEdit, QFormLayout, 
                             QFileDialog, QLabel)


class FileBrowser(QDialog):

    def __init__(self, *args, **kwargs):
        super(FileBrowser, self).__init__(*args, **kwargs)
        
        self.setWindowTitle("Open Files")
        self.setGeometry(100,100, 800,200)
        
        self.button_opennd2 = QPushButton('Open image file')
        self.button_opennd2.setEnabled(True)
        self.button_opennd2.clicked.connect(self.getnd2path)
        self.button_opennd2.setToolTip("Browse for an image file")
        self.button_opennd2.setMaximumWidth(150)
        
        self.button_openfolder = QPushButton('Open image folder')
        self.button_openfolder.setEnabled(True)
        self.button_openfolder.clicked.connect(self.getfolder)
        self.button_openfolder.setToolTip("Browse for folder with images")
        self.button_openfolder.setMaximumWidth(150)
        
        self.button_openhdf = QPushButton('Open mask file')
        self.button_openhdf.setEnabled(True)
        self.button_openhdf.clicked.connect(self.gethdfpath)
        self.button_openhdf.setToolTip("Browse for a mask file")
        self.button_openhdf.setMaximumWidth(150)
        
        self.newhdfentry = QLineEdit()
        self.newhdfentry.setText("newmaskfile")

        self.nd2name = ''
        self.hdfname = ''
        flo = QFormLayout()
        
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)


        self.labelnd2 = QLabel()
        self.labelnd2.setText('No image file (.nd2, .tif, .tiff) selected')
        
        self.labelhdf = QLabel()
        self.labelhdf.setText('No mask file (.h5, .tif, .tiff) selected')
        
        self.labelfolder = QLabel()
        self.labelfolder.setText('No folder selected')
        
        flo.addRow(self.labelnd2, self.button_opennd2)
        flo.addRow(self.labelfolder, self.button_openfolder)
        flo.addRow(self.labelhdf, self.button_openhdf)
        flo.addRow('If no hdf file already exists, give a name to create a new file', self.newhdfentry)
        
        flo.addWidget(self.buttonBox)
       
        self.setLayout(flo)
        
        
        

    def getnd2path(self):
        self.nd2name,_ = QFileDialog.getOpenFileName(self, 'Open image file','', 
            'Image files (*.nd2 *.tif *.tiff *.tiff *.jpg *.jpeg *.png *.bmp '
                          '*.pbm *.pgm *.ppm *.pxm *.pnm *.jp2)')
        if self.nd2name != '':
            self.labelnd2.setText(self.nd2name)
            self.labelfolder.setText('')
      
    def gethdfpath(self):
        self.hdfname,_ = QFileDialog.getOpenFileName(self,'Open mask file','', 'Mask files (*.h5 *.tif *.tiff)')
        if self.hdfname != '':
            self.labelhdf.setText(self.hdfname)
            self.newhdfentry.setText("")
        
    def getfolder(self):
        self.nd2name = QFileDialog.getExistingDirectory(self, ("Select Image Folder"))
        if self.nd2name != '':
            self.labelfolder.setText(self.nd2name)
            self.labelnd2.setText('')
