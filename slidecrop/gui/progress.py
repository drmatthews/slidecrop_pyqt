from PyQt5 import QtCore, QtGui, QtWidgets

import slidecrop.gui.progress_ui as UI


class Progress(QtWidgets.QMainWindow):
    def __init__(self, parent, max_val, title):
        super(Progress, self).__init__(parent)
        self.parent = parent
        self.ui = UI.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle('{} progress'.format(title))
        self.ui.progress.setMaximum(max_val)

    def updateBar(self, value):
        self.ui.progress.setValue(value)