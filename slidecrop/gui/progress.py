from PyQt5 import QtCore, QtGui, QtWidgets

from . import progress_ui as UI


class Progress(QtWidgets.QDialog):
    def __init__(self, parent, max_val, title):
        super(Progress, self).__init__(parent)
        self.parent = parent
        self.ui = UI.Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowTitle('{} progress'.format(title))
        self.ui.progress.setMaximum(max_val)

    def updateBar(self, value):
        self.ui.progress.setValue(value)