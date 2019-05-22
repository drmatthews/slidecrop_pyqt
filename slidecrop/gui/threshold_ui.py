# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'slidecrop\resources\threshold.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ThresholdDialog(object):
    def setupUi(self, ThresholdDialog):
        ThresholdDialog.setObjectName("ThresholdDialog")
        ThresholdDialog.resize(299, 179)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/newPrefix/icon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        ThresholdDialog.setWindowIcon(icon)
        self.verticalLayout = QtWidgets.QVBoxLayout(ThresholdDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.histogram_widget = GraphicsLayoutWidget(ThresholdDialog)
        self.histogram_widget.setObjectName("histogram_widget")
        self.verticalLayout.addWidget(self.histogram_widget)
        self.method_combo = QtWidgets.QComboBox(ThresholdDialog)
        self.method_combo.setObjectName("method_combo")
        self.method_combo.addItem("")
        self.method_combo.addItem("")
        self.method_combo.addItem("")
        self.method_combo.addItem("")
        self.method_combo.addItem("")
        self.verticalLayout.addWidget(self.method_combo)

        self.retranslateUi(ThresholdDialog)
        QtCore.QMetaObject.connectSlotsByName(ThresholdDialog)

    def retranslateUi(self, ThresholdDialog):
        _translate = QtCore.QCoreApplication.translate
        ThresholdDialog.setWindowTitle(_translate("ThresholdDialog", "Threshold"))
        self.method_combo.setItemText(0, _translate("ThresholdDialog", "Isodata"))
        self.method_combo.setItemText(1, _translate("ThresholdDialog", "Mean"))
        self.method_combo.setItemText(2, _translate("ThresholdDialog", "Otsu"))
        self.method_combo.setItemText(3, _translate("ThresholdDialog", "Triangle"))
        self.method_combo.setItemText(4, _translate("ThresholdDialog", "Yen"))


from pyqtgraph import GraphicsLayoutWidget
from .. resources import resources_rc
