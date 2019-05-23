import os

from PyQt5 import QtCore, QtGui, QtWidgets

from . import batch_ui as batch_UI
from .progress import Progress
from .threads import ThresholdWorker
from .threads import SegmentationWorker
from .threads import BatchSegmentationWorker
from .threads import BatchSlideParseWorker
from .threads import BatchCropWorker
from .roi import ROIItem


class BatchTable(QtWidgets.QWidget):

    def __init__(self, parent, dialog=None, table_widget=None):

        super(BatchTable, self).__init__(table_widget)
        self.parent = parent
        self.dialog = dialog
        self.table_widget = table_widget
        self.table_widget.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self.table_widget.setSelectionMode(QtWidgets.QTableView.SingleSelection)

        self.thresh_worker = ThresholdWorker()
        self.thresh_worker.threshold_finished.connect(self.updateThresholdCell)

        self.segmentation_worker = SegmentationWorker()
        self.segmentation_worker.segmentation_finished.connect(self.updateSlideViewer)

    def update(self, folder, channels, thresholds):
        self.table_widget.clear()
        if folder:
            file_count = 0
            for f in os.listdir(folder):
                if f.endswith('.ims'):
                    file_count += 1

            self.table_widget.setRowCount(file_count)
            self.table_widget.setColumnCount(7)
            self.table_widget.setHorizontalHeaderLabels(
                ['Progress', 'Filename', 'Channels', 'Segmentation Channel',
                 'Thresholds', 'Threshold method', '']
            )

            # should probably make column numbers globals
            header = self.table_widget.horizontalHeader()
            rid = 0
            self.bars = []
            self.combos = []
            self.preview_btns = []
            for filename in os.listdir(folder):
                if filename.endswith('.ims'):

                    # add progress bar cell
                    bar = QtWidgets.QProgressBar()
                    bar.setValue(0)
                    bar.setTextVisible(True)
                    self.bars.append(bar)
                    self.table_widget.setCellWidget(rid, 0, bar)
                    header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
                    
                    # add filename cell
                    fname = QtWidgets.QTableWidgetItem('{}'.format(filename))
                    fname.setFlags(QtCore.Qt.ItemIsEnabled)
                    self.table_widget.setItem(rid, 1, fname)
                    header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
                    
                    # add channel cell
                    chan = QtWidgets.QTableWidgetItem('{}'.format(channels[rid]))
                    chan.setFlags(QtCore.Qt.ItemIsEnabled)
                    self.table_widget.setItem(rid, 2, chan)
                    header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)

                    # add segmentation channel cell
                    seg_chan = QtWidgets.QTableWidgetItem('0')
                    self.table_widget.setItem(rid, 3, seg_chan)
                    header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)                    

                    # add threshold values cell
                    thresh = QtWidgets.QTableWidgetItem('{}'.format(thresholds[rid]))
                    self.table_widget.setItem(rid, 4, thresh)
                    header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)

                    # add threshold method cell
                    combo = QtWidgets.QComboBox()
                    combo_items = ['Isodata', 'Mean', 'Otsu', 'Triangle', 'Yen']
                    combo.addItems(combo_items)
                    combo.setCurrentIndex(2)
                    combo.currentIndexChanged.connect(self.methodChanged)
                    self.combos.append(combo)
                    self.table_widget.setCellWidget(rid, 5, combo)
                    header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)   
              
                    # add threshold method cell
                    btn = QtWidgets.QPushButton()
                    btn.setText('Preview')
                    btn.clicked.connect(self.previewClicked)
                    self.preview_btns.append(btn)
                    self.table_widget.setCellWidget(rid, 6, btn)
                    header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeToContents)
                    
                    rid += 1

    def methodChanged(self):
        """
        Triggered when a combo box in the table changed
        """
        # get the row number
        selected_rows = self.table_widget.selectionModel().selectedRows()
        rid = selected_rows[0].row()

        # get the filename and create path to slide
        filename = self.table_widget.item(rid, 1).text()
        slide_path = os.path.join(self.dialog.folder, filename)
        method = self.combos[rid].currentText().lower()

        # lauch a threshold worker to recalculate the
        # channel thresholds
        self.thresh_worker.initialise(slide_path, method=method)
        self.thresh_worker.start()

    def updateThresholdCell(self, result):
        # get the row number
        selected_rows = self.table_widget.selectionModel().selectedRows()
        rid = selected_rows[0].row()

        thresholds = ', '.join('{:.2f}'.format(t) for t in result)
        item = QtWidgets.QTableWidgetItem('{}'.format(thresholds))
        self.table_widget.setItem(rid, 4, item)

    def updateThreshMethodCell(self, val):
        # get the row number
        selected_rows = self.table_widget.selectionModel().selectedRows()
        rid = selected_rows[0].row()

        method = self.combos[rid]
        method.setCurrentIndex(val)

    def previewClicked(self):
        # get the row number
        selected_rows = self.table_widget.selectionModel().selectedRows()
        rid = selected_rows[0].row()

        # get the filename and create path to slide
        filename = self.table_widget.item(rid, 1).text()
        slide_path = os.path.join(self.dialog.folder, filename)

        self.parent.importImage(slide_path)
        self._runSegmentation()

    def updateSlideViewer(self, result):
        if result:
            rois = []
            for r in result:
                roi = ROIItem(self.parent, QtCore.QRectF(*r.roi))
                rois.append(roi)
                self.parent.viewer.addROI(roi)

            self.parent.rois = rois
            self.parent.roi_table.update(rois)
            self.parent.scaled_regions = result

    def getRows(self):
        rows = []
        for r in range(self.table_widget.rowCount()):
            row = []
            # get slide path from second column
            row.append(self.table_widget.item(r, 1).text())
            # get the number of channels from the third
            row.append(int(self.table_widget.item(r, 2).text()))
            # get the segmentation channel from the fourth
            row.append(int(self.table_widget.item(r, 3).text()))            
            # get the threshold values as a list from the fifth
            row.append(self._getThresholdCell(r))
            rows.append(row)
        return rows

    def _getThresholdCell(self, row):
        thresh_str = self.table_widget.item(row, 4).text()
        return [float(t) for t in thresh_str.split(',')]

    def _runSegmentation(self):
        selected_rows = self.table_widget.selectionModel().selectedRows()
        rid = selected_rows[0].row()

        # get the filename and create path to slide
        filename = self.table_widget.item(rid, 1).text()
        slide_path = os.path.join(self.dialog.folder, filename)
        seg_channel = int(self.table_widget.item(rid, 3).text())        
        threshold = self._getThresholdCell(rid)[seg_channel]

        self.segmentation_worker.initialise(slide_path, seg_channel, threshold)
        self.segmentation_worker.start()


class BatchDialog(QtWidgets.QDialog):
    def __init__(self, parent, folder=None):
        super(BatchDialog, self).__init__(parent)
        self.parent = parent
        self.folder = folder
        # self.channels = []
        # self.thresholds = ''
        self.threshold_method = 'otsu'
        
        self.init_ui()

        if folder:
            self.ui.folder_edit.setText(folder)
            self.parseSlides(folder, self.threshold_method)
        else:
            self.restoreTable()

    def init_ui(self):
        self.ui = batch_UI.Ui_Dialog()
        self.ui.setupUi(self)

        self.batch_table = BatchTable(self.parent, self, self.ui.batch_table_widget)

        self.ui.folder_btn.clicked.connect(self.folderClicked)
        self.ui.run_btn.clicked.connect(self.runClicked)
        # self.ui.stop_btn.clicked.connect(self.stopClicked)
        self.ui.stop_btn.hide()

        self.import_worker = BatchSlideParseWorker()
        self.import_worker.parse_done.connect(self.updateParameters)
        self.import_worker.parse_done[str].connect(self.parseCancelled)

        self.worker = BatchCropWorker()
        self.worker.segmentation_finished.connect(self.setTableBarMax)
        self.worker.batch_progress.connect(self.updateTableProgressBars)
        self.worker.finished.connect(self.batchFinished)

    def closeEvent(self, event):
        self.saveTable()
        if self.parent.curr_img is not None:
            self.parent.curr_img = None
            self.parent.curr_channel = 0
            self.parent.threshold = []
            self.parent.viewer.clearScene()            
            self.parent.viewer.clear()
        
        print(len(self.parent.rois))
        if self.parent.rois:
            self.parent.rois = []
            self.parent.scaled_regions = []
            self.parent.roi_table.clear()

        return super().closeEvent(event)

    def folderClicked(self):
        folder = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        if folder:
            self.folder = folder
            self.ui.folder_edit.setText(folder)
            self.parseSlides(folder, self.threshold_method)

    def runClicked(self):
        # get the rows from the table
        # form the lists for passing to the batch worker thread
        # this is very convoluted and might benefit from using
        # pyqt's MVC framework

        # the case that a user edits the thresholds and the
        # number of comma separated values that remain
        # does not match the number of channels in the image
        # is not covered
        self.ui.run_btn.setEnabled(False)
        self.ui.stop_btn.setEnabled(True)
        rows = self.batch_table.getRows()
        try:
            input_paths = []
            output_dirs = []
            seg_channels = []            
            thresholds = []
            threshold_methods = []
            for row in rows:
                filename = row[0]
                input_paths.append(os.path.join(self.folder, filename))
                output_dirs.append(self.folder)
                seg_channel = row[2]
                seg_channels.append(seg_channel)
                thresholds.append(row[3][seg_channel])
            self._runBatch(
                input_paths, output_dirs,
                seg_channels, thresholds
            )
        except:
            pass

    def stopClicked(self):
        if self.ui.stop_btn.isEnabled():
            if not self.worker.is_stopped():
                self.worker.stop()
                for bar in self.batch_table.bars:
                    bar.setValue(0)

    def parseSlides(self, folder, method):
        if os.path.isdir(folder):
            count = 0
            for filename in os.listdir(folder):
                if filename.endswith('.ims'):
                    count += 1
            self.import_progress = Progress(self, count - 1, 'Slide import')
            self.import_worker.initialise(folder, method)
            self.import_worker.progress.connect(self.updateImportProgress)
            self.import_worker.finished.connect(self.importFinished)
            self.import_worker.start()

            if not self.import_progress.isVisible():          
                self.import_progress.show()

    def parseCancelled(self):
        print("import didn't work")
        self.channels = ''
        self.thresholds = ''

    def setTableBarMax(self, val):
        bar = self.batch_table.bars[val[0]]
        bar.setMaximum(val[1] - 1)

    def updateTableProgressBars(self, val):
        bar = self.batch_table.bars[val[0]]
        bar.setValue(val[1])

    def updateImportProgress(self, val):
        if self.import_progress.isVisible():
            self.import_progress.updateBar(val)        

    def batchFinished(self):
        self.ui.run_btn.setEnabled(True)
        self.ui.stop_btn.setEnabled(False)
        for bar in self.batch_table.bars:
            bar.setValue(0)

    def importFinished(self):
        if self.import_progress.isVisible():
            self.import_progress.close()

    def updateParameters(self, results):
        if results:
            channels = [str(c) for c in results[0]]
            thresholds = []
            for thresh in results[1]:
                thresholds.append(', '.join('{:.2f}'.format(t) for t in thresh))

            self.batch_table.update(self.folder, channels, thresholds)
            self.channels = channels
            self.thresholds = thresholds

    def restoreTable(self):
        settings = QtCore.QSettings('Dan', 'slidecrop')
        self.folder = settings.value('folder', type=str)
        self.channels = settings.value('channels', type=list)

        self.thresholds = settings.value('thresholds', type=list)
        if self.channels and self.thresholds:
            self.ui.folder_edit.setText(self.folder)
            self.batch_table.update(self.folder, self.channels, self.thresholds)

    def saveTable(self):
        settings = QtCore.QSettings('Dan', 'slidecrop')
        settings.setValue('folder', self.folder)
        settings.setValue('channels', self.channels)
        settings.setValue('thresholds', self.thresholds)


    def _runBatch(self, input_paths, output_dirs, seg_channels, thresholds):
        self.worker.initialise(input_paths, output_dirs, seg_channels, thresholds)
        self.worker.start()