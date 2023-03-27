from PyQt5.QtWidgets import QApplication, QDialog, QProgressBar, QVBoxLayout, QPushButton, QLabel
import time

class ProgressBar(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        # set the dialog to be a modal that blocks input to the main window
        self.setModal(True)

        # set the title of the dialog
        self.setWindowTitle("Progress")

        # create a progress bar widget
        self.progress = QProgressBar(self)

        # set the minimum and maximum values of the progress bar
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)

        # create a label widget to display the progress status
        self.status = QLabel("Processing...", self)

        # create a layout to add the widgets to
        layout = QVBoxLayout(self)
        layout.addWidget(self.status)
        layout.addWidget(self.progress)
        self.setLayout(layout)

        # set initial value
        self.progress.setValue(0)
        self.status.setText("Processing...")

        # show the dialog
        self.show()

    def update_progress(self, value):
        self.progress.setValue(value)
    def set_status(self, t):
        self.status.setText("Processing... {}%".format(t))