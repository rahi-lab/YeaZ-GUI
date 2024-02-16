
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
        
        self.mic_type = QComboBox()
        self.mic_type.addItem("Image type", None)
        self.mic_type.addItem("Bright-field budding yeast", "bf")
        self.mic_type.addItem("Phase contrast budding yeast", "pc")
        self.mic_type.addItem("Bud phase contrast fission", "fission")

        self.mic_type.setCurrentIndex(0)
        flo.addRow("Select image type: ", self.mic_type)   
        
        
        self.tracker = QComboBox()
        self.tracker.addItem("old-fashion but fast, Hungarian algorithm","Hungarian")
        self.tracker.addItem ("new-fashion but slower with a lot of cells, Graph Convolutional Network","GCN",)
        self.tracker.setCurrentIndex(0)
        flo.addRow("Select the algorithm for tracking cells: ", self.tracker)     
        
        QBtn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        flo.addWidget(self.buttonBox)
        self.setLayout(flo)
        