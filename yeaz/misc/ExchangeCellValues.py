# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 17:38:58 2019
"""

from PyQt6.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget, QPushButton, QComboBox, QDialog, QDialogButtonBox, QInputDialog, QLineEdit, QFormLayout
from PyQt6 import QtGui
from PyQt6.QtGui import QShortcut
from PyQt6.QtCore import pyqtSignal, QObject, Qt
#import PyQt package, allows for GUI interactions

class CustomDialog(QDialog):

    def __init__(self, *args, **kwargs):
        super(CustomDialog, self).__init__(*args, **kwargs)
        
        self.setWindowTitle("Exchange Cell Values")
        self.setGeometry(100,100, 500,200)
        
        self.entry1 = QLineEdit()
        self.entry1.setValidator(QtGui.QIntValidator())
        self.entry1.setMaxLength(4)
        self.entry1.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.entry2 = QLineEdit()
        self.entry2.setValidator(QtGui.QIntValidator())
        self.entry2.setMaxLength(4)
        self.entry2.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        flo = QFormLayout()
        flo.addRow('Enter Cell value 1 (integer):', self.entry1)
        flo.addRow('Enter Cell value 2 (integer):', self.entry2)        
        
        QBtn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

#        self.layout = QVBoxLayout()
#        self.layout.addWidget(self.buttonBox
        flo.addWidget(self.buttonBox)
        self.setLayout(flo)
        
