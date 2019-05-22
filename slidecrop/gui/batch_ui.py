# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'slidecrop\resources\batch.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(698, 272)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/newPrefix/icon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Dialog.setWindowIcon(icon)
        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.folder_edit = QtWidgets.QLineEdit(Dialog)
        self.folder_edit.setReadOnly(True)
        self.folder_edit.setObjectName("folder_edit")
        self.horizontalLayout_3.addWidget(self.folder_edit)
        self.folder_btn = QtWidgets.QPushButton(Dialog)
        self.folder_btn.setObjectName("folder_btn")
        self.horizontalLayout_3.addWidget(self.folder_btn)
        self.gridLayout.addLayout(self.horizontalLayout_3, 0, 0, 1, 1)
        self.batch_table_widget = QtWidgets.QTableWidget(Dialog)
        self.batch_table_widget.setObjectName("batch_table_widget")
        self.batch_table_widget.setColumnCount(0)
        self.batch_table_widget.setRowCount(0)
        self.gridLayout.addWidget(self.batch_table_widget, 1, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.stop_btn = QtWidgets.QPushButton(Dialog)
        self.stop_btn.setObjectName("stop_btn")
        self.horizontalLayout_2.addWidget(self.stop_btn)
        self.run_btn = QtWidgets.QPushButton(Dialog)
        self.run_btn.setObjectName("run_btn")
        self.horizontalLayout_2.addWidget(self.run_btn)
        self.gridLayout.addLayout(self.horizontalLayout_2, 2, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Batch"))
        self.folder_btn.setText(_translate("Dialog", "..."))
        self.stop_btn.setText(_translate("Dialog", "Stop"))
        self.run_btn.setText(_translate("Dialog", "Run"))


from .. resources import resources_rc
