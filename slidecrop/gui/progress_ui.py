# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'slidecrop\resources\progress.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(371, 61)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/newPrefix/icon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        self.progress = QtWidgets.QProgressBar(Dialog)
        self.progress.setGeometry(QtCore.QRect(30, 20, 321, 21))
        self.progress.setProperty("value", 0)
        self.progress.setObjectName("progress")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Progress"))


from .. resources import resources_rc
