from PyQt5 import QtCore, QtGui, QtWidgets

import slidecrop.gui.crop_ui as UI


class CropProgress(QtWidgets.QMainWindow):
    def __init__(self, parent, num_regions):
        super(CropProgress, self).__init__(parent)
        self.parent = parent
        self.ui = UI.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.crop_progress.setMaximum(num_regions - 1)

    def updateBar(self, value):
        self.ui.crop_progress.setValue(value)