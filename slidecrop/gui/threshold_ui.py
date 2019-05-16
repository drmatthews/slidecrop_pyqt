# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'slidecrop\resources\threshold.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(299, 178)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/newPrefix/icon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.histogram_widget = QtWidgets.QWidget(self.centralwidget)
        self.histogram_widget.setObjectName("histogram_widget")
        self.verticalLayout.addWidget(self.histogram_widget)
        self.method_combo = QtWidgets.QComboBox(self.centralwidget)
        self.method_combo.setObjectName("method_combo")
        self.method_combo.addItem("")
        self.method_combo.addItem("")
        self.method_combo.addItem("")
        self.method_combo.addItem("")
        self.method_combo.addItem("")
        self.verticalLayout.addWidget(self.method_combo)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Threshold"))
        self.method_combo.setItemText(0, _translate("MainWindow", "Isodata"))
        self.method_combo.setItemText(1, _translate("MainWindow", "Mean"))
        self.method_combo.setItemText(2, _translate("MainWindow", "Otsu"))
        self.method_combo.setItemText(3, _translate("MainWindow", "Triangle"))
        self.method_combo.setItemText(4, _translate("MainWindow", "Yen"))


from .. resources import resources_rc
