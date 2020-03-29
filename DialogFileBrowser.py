# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 17:38:58 2019
"""

from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget, QPushButton, QShortcut, QComboBox, QDialog, QDialogButtonBox, QInputDialog, QLineEdit, QFormLayout, QFileDialog, QLabel
from PyQt5 import QtGui
#from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import pyqtSignal, QObject, Qt
#import PyQt package, allows for GUI interactions

class FileBrowser(QDialog):

    def __init__(self, *args, **kwargs):
        super(FileBrowser, self).__init__(*args, **kwargs)
        
        self.setWindowTitle("Open Files")
        self.setGeometry(100,100, 800,200)
        
        
        self.button_opennd2 = QPushButton('Open nd2 file')
        self.button_opennd2.setEnabled(True)
        self.button_opennd2.clicked.connect(self.getnd2path)
        self.button_opennd2.setToolTip("Browse for an nd2 file")
        self.button_opennd2.setMaximumWidth(150)
        
        self.button_openhdf = QPushButton('Open hdf file')
        self.button_openhdf.setEnabled(True)
        self.button_openhdf.clicked.connect(self.gethdfpath)
        self.button_openhdf.setToolTip("Browse for an hdf file containing the masks")
        self.button_openhdf.setMaximumWidth(150)
        
        self.newhdfentry = QLineEdit()
#        self.newhdfentry(Qt.AlignLeft)



        self.nd2name = ''
        self.hdfname = ''
#        
        flo = QFormLayout()
#        flo.addRow('Enter Cell value 1 (integer):', self.entry1)
                
        
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)


        self.labelnd2 = QLabel()
        self.labelnd2.setText('No nd2 file selected')
        
        self.labelhdf = QLabel()
        self.labelhdf.setText('No hdf file selected')
        flo.addRow(self.labelnd2, self.button_opennd2)
        flo.addRow(self.labelhdf, self.button_openhdf)
#        flo.addWidget(self.button_openhdf)
        flo.addRow('If no hdf file already exists, give a name to create a new file', self.newhdfentry)
        
        flo.addWidget(self.buttonBox)
       
        self.setLayout(flo)
        
        
        

    def getnd2path(self):
      self.nd2name,_ = QFileDialog.getOpenFileName(self, 'Open .nd2 File','', 'nd2 Files (*.nd2)')
#      print(self.nd2name)
#      print(self.nd2name)
      self.labelnd2.setText(self.nd2name)
      
    def gethdfpath(self):
        self.hdfname,_ = QFileDialog.getOpenFileName(self,'Open .hdf File','', 'hdf Files (*.h5)')
        self.labelhdf.setText(self.hdfname)
        