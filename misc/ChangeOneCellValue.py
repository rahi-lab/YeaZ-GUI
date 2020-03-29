# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 17:38:58 2019
"""

from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget, QPushButton, QShortcut, QComboBox, QDialog, QDialogButtonBox, QInputDialog, QLineEdit, QFormLayout
from PyQt5 import QtGui
#from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import pyqtSignal, QObject, Qt
#import PyQt package, allows for GUI interactions

class CustomDialog(QDialog):

    def __init__(self, *args, **kwargs):
        super(CustomDialog, self).__init__(*args, **kwargs)
        
        self.setWindowTitle("Change Value one cell")
        self.setGeometry(100,100, 500,200)
        
        self.entry1 = QLineEdit()
        self.entry1.setValidator(QtGui.QIntValidator())
        self.entry1.setMaxLength(4)
        self.entry1.setAlignment(Qt.AlignRight)
        
#        self.entry2 = QLineEdit()
#        self.entry2.setValidator(QtGui.QIntValidator())
#        self.entry2.setMaxLength(4)
#        self.entry2.setAlignment(Qt.AlignRight)
        
        flo = QFormLayout()
        flo.addRow('Enter Cell value (integer):', self.entry1)
#        flo.addRow('Enter Cell value 2 (integer):', self.entry2)        
        
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

#        self.layout = QVBoxLayout()
#        self.layout.addWidget(self.buttonBox
        flo.addWidget(self.buttonBox)
        self.setLayout(flo)
        