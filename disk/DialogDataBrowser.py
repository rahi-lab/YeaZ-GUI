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
        
        self.setWindowTitle("Data file")
        self.setGeometry(100,100, 800,200)
        
        
        self.button_openxls = QPushButton('Open excel file')
        self.button_openxls.setEnabled(True)
        self.button_openxls.clicked.connect(self.getxlspath)
        self.button_openxls.setToolTip("Browse for an xls file")
        self.button_openxls.setMaximumWidth(150)
        

        
        self.newxlsentry = QLineEdit()

        self.xlsname = ''
#        
        flo = QFormLayout()
#        flo.addRow('Enter Cell value 1 (integer):', self.entry1)
                
        
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)


        self.labelxls = QLabel()
        self.labelxls.setText('No xls file selected')

        flo.addRow(self.labelxls, self.button_openxls)

#        flo.addWidget(self.button_openhdf)
        flo.addRow('If no xls data file already exists, give a name to create a new file', self.newxlsentry)
        
        flo.addWidget(self.buttonBox)
       
        self.setLayout(flo)
        
        
        

    def getxlspath(self):
      self.xlsname,_ = QFileDialog.getOpenFileName(self, 'Open .xls File','', 'xls Files (*.xls)')
#      print(self.nd2name)
#      print(self.nd2name)
      self.labelxls.setText(self.xlsname)

        
