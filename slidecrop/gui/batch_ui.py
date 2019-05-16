# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'slidecrop\resources\batch.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(698, 272)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/newPrefix/icon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.batch_table_widget = QtWidgets.QTableWidget(self.centralwidget)
        self.batch_table_widget.setObjectName("batch_table_widget")
        self.batch_table_widget.setColumnCount(0)
        self.batch_table_widget.setRowCount(0)
        self.gridLayout.addWidget(self.batch_table_widget, 5, 0, 1, 1)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.folder_edit = QtWidgets.QLineEdit(self.centralwidget)
        self.folder_edit.setReadOnly(True)
        self.folder_edit.setObjectName("folder_edit")
        self.horizontalLayout_3.addWidget(self.folder_edit)
        self.folder_btn = QtWidgets.QPushButton(self.centralwidget)
        self.folder_btn.setObjectName("folder_btn")
        self.horizontalLayout_3.addWidget(self.folder_btn)
        self.gridLayout.addLayout(self.horizontalLayout_3, 0, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.stop_btn = QtWidgets.QPushButton(self.centralwidget)
        self.stop_btn.setObjectName("stop_btn")
        self.horizontalLayout_2.addWidget(self.stop_btn)
        self.run_btn = QtWidgets.QPushButton(self.centralwidget)
        self.run_btn.setObjectName("run_btn")
        self.horizontalLayout_2.addWidget(self.run_btn)
        self.gridLayout.addLayout(self.horizontalLayout_2, 6, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Batch"))
        self.folder_btn.setText(_translate("MainWindow", "..."))
        self.stop_btn.setText(_translate("MainWindow", "Stop"))
        self.run_btn.setText(_translate("MainWindow", "Run"))


import slidecrop.resources.resources_rc
