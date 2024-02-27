
from PyQt6.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget, QPushButton, QComboBox, QDialog, QDialogButtonBox, QInputDialog, QLineEdit, QFormLayout, QLabel
from PyQt6 import QtGui
from PyQt6.QtGui import QShortcut
from PyQt6.QtCore import pyqtSignal, QObject, Qt
#import PyQt package, allows for GUI interactions

class CustomDialog(QDialog):

    def __init__(self, *args, **kwargs):
        super(CustomDialog, self).__init__(*args, **kwargs)
        app, = args
        self.setWindowTitle("Retrack")
        self.setGeometry(100,100, 500,200)
        
        self.entry1 = QLineEdit()
        self.entry1.setValidator(QtGui.QIntValidator())
        self.entry1.setMaxLength(4)
        self.entry1.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.labeltime = QLabel("Enter a frame number between {} to {}".format(app.Tindex+1, app.reader.sizet-1))
        flo = QFormLayout()
        flo.addWidget(self.labeltime)
        flo.addRow('retracking frames from {} (next frame) to '.format(app.Tindex+1), self.entry1)       
        
        QBtn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        flo.addWidget(self.buttonBox)
        self.setLayout(flo)
        
        # Set focus to entry1
        self.entry1.setFocus()
        