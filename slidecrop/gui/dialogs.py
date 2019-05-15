import os

from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

from numpy import arange, max, nonzero

import slidecrop.gui.threshold_ui as thresh_UI
import slidecrop.gui.segmentation_ui as seg_UI
import slidecrop.gui.batch_ui as batch_UI
from slidecrop.gui.progress import Progress
from slidecrop.gui.threads import ThresholdWorker
from slidecrop.gui.threads import SegmentationWorker
from slidecrop.gui.threads import BatchSegmentationWorker
from slidecrop.gui.threads import BatchSlideParseWorker
from slidecrop.gui.threads import BatchCropWorker
from slidecrop.gui.roi import ROIItem

pg.setConfigOptions(antialias=True)
pg.setConfigOption('background', (240, 240, 240))
pg.setConfigOption('foreground', 'k')


class ThresholdLine(pg.InfiniteLine):
    def __init__(self, threshold):
        defaults = dict(
            bounds=(0, 255),
            movable=True,
            angle=90,
            label='threshold={value:0.2f}', 
            labelOpts={
                'position':0.1,
                'color': (200,200,100),
                'fill': (200,200,200,50),
            'movable': True}
        )
        super(ThresholdLine, self).__init__(pos=threshold, **defaults)

class HistogramGraph(pg.GraphicsLayoutWidget):
    def __init__(self, parent, data, threshold):
        super(HistogramGraph, self).__init__(parent)

        self.data = data
        self.threshold = threshold

        grad = QtGui.QLinearGradient(0, 0, 0, 3)
        grad.setColorAt(0.1, pg.mkColor('#000000'))
        grad.setColorAt(0.9, pg.mkColor((156, 220, 218)))
        self.fillbrush = (30, 30, 30)
        self.linepen = (200, 200, 100)

        self.resize(279, 139)

    def plot(self):
        self.clear()
        self.p = self.addPlot()
        self.p.setMenuEnabled(False)

        xdata = arange(256)
        ydata = self.data
        # ydata = ydata[nonzero(ydata)]
        # xdata = xdata[nonzero(ydata)]
        ymax = max(ydata)
        self.thresh_line = ThresholdLine(self.threshold)

        self.p.plot(xdata, ydata, pen=self.linepen, brush=self.fillbrush, fillLevel=0)
        self.p.setXRange(50, 255, padding=0)
        self.p.setYRange(1, ymax, padding=0)
        self.p.setLogMode(False, True)
        self.p.setLimits(xMin=0, xMax=255, yMin=1, yMax=ymax)
        self.p.hideAxis('left')
        self.p.hideAxis('bottom')
        self.p.addItem(self.thresh_line)


class ThresholdDialog(QtWidgets.QMainWindow):
    def __init__(self, parent, data, threshold):
        super(ThresholdDialog, self).__init__(parent)
        self.parent = parent
        self.ui = thresh_UI.Ui_MainWindow()
        self.ui.setupUi(self)
        self.histogram = HistogramGraph(self.ui.histogram_widget, data, threshold)

    def closeEvent(self, event):
        dchannel = self.parent.curr_channel
        self.parent._updateDisplayImage(dchannel, show_mask=False)


class SegmentationDialog(QtWidgets.QMainWindow):
    def __init__(self, parent, slide_path, channel_names, threshold):
        super(SegmentationDialog, self).__init__(parent)
        self.parent = parent
        self.slide_path = slide_path
        self.threshold = threshold
        self.ui = seg_UI.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.segment_button.clicked.connect(self.runClicked)

        self.ui.channel_combo.addItems(channel_names)

    def runClicked(self):
        self.parent.viewer.clear_scene()
        segment_channel = self.ui.channel_combo.currentIndex()
        threshold = self.threshold[segment_channel]

        self.segmentation_worker = SegmentationWorker(
            self.slide_path, segment_channel, threshold
        )
        self.segmentation_worker.segmentation_finished.connect(self.onSegmentationFinished)     
        self.segmentation_worker.start()

    def onSegmentationFinished(self, result):
        if result:
            rois = []
            for r in result:
                roi = ROIItem(self.parent, QtCore.QRectF(*r.roi))
                rois.append(roi)
                self.parent.viewer.addROI(roi)

            self.parent.roi_table.update(rois)
            self.parent.roi_table.get_checked_rows()


class BatchTable(QtWidgets.QWidget):

    def __init__(self, parent=None, table_widget=None):

        super(BatchTable, self).__init__(table_widget)
        self.parent = parent
        self.table_widget = table_widget
        self.table_widget.setSelectionBehavior(QtWidgets.QTableView.SelectRows)

    def update(self, folder, channels, thresholds):
        self.table_widget.clear()
        if folder:
            file_count = 0
            for f in os.listdir(folder):
                if f.endswith('.ims'):
                    file_count += 1

            self.table_widget.setRowCount(file_count)
            self.table_widget.setColumnCount(5)
            self.table_widget.setHorizontalHeaderLabels(['Filename', 'Channels', 'Thresholds', 'Segmentation Channel', ''])

            header = self.table_widget.horizontalHeader()
            rid = 0
            self.bars = []
            for filename in os.listdir(folder):
                if filename.endswith('.ims'):
                    fname = QtWidgets.QTableWidgetItem('{}'.format(filename))
                    fname.setFlags(QtCore.Qt.ItemIsEnabled)
                    self.table_widget.setItem(rid, 0, fname)
                    header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)

                    chan = QtWidgets.QTableWidgetItem('{}'.format(channels[rid]))
                    chan.setFlags(QtCore.Qt.ItemIsEnabled)
                    self.table_widget.setItem(rid, 1, chan)
                    header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)

                    thresh = QtWidgets.QTableWidgetItem('{}'.format(thresholds[rid]))
                    self.table_widget.setItem(rid, 2, thresh)
                    header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)

                    seg_chan = QtWidgets.QTableWidgetItem('0')
                    self.table_widget.setItem(rid, 3, seg_chan)
                    header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)

                    bar = QtWidgets.QProgressBar()
                    self.bars.append(bar)
                    self.table_widget.setCellWidget(rid, 4, bar)
                    header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)              
                    
                    rid += 1          

    def tableBtnClick(self):
        pass

    def _thresholdCell(self, row):
        thresh_str = self.table_widget.item(row, 2).text()
        return [float(t) for t in thresh_str.split(',')]

    def getRows(self):
        rows = []
        for r in range(self.table_widget.rowCount()):
            row = []
            # get slide path from first column
            row.append(self.table_widget.item(r, 0).text())
            # get the number of channels from the second
            row.append(int(self.table_widget.item(r, 1).text()))
            # get the threshold values as a list from the third
            row.append(self._thresholdCell(r))
            # get the segmentation channel from the fourth
            row.append(int(self.table_widget.item(r, 3).text()))
            rows.append(row)
        return rows


class BatchDialog(QtWidgets.QMainWindow):
    def __init__(self, parent, folder=None):
        super(BatchDialog, self).__init__(parent)
        self.parent = parent
        self.folder = folder
        self.channels = []
        self.thresholds = []
        
        self.init_ui()

        if folder:
            self.ui.folder_edit.setText(folder)
            self._parseSlides(folder)

    def init_ui(self):
        self.ui = batch_UI.Ui_MainWindow()
        self.ui.setupUi(self)
        self.batch_table = BatchTable(self, self.ui.batch_table_widget)

        self.ui.folder_btn.clicked.connect(self.folderClicked)
        self.ui.run_btn.clicked.connect(self.runClicked)
        # self.ui.stop_btn.clicked.connect(self.stopClicked)
        self.ui.stop_btn.hide()

        self.import_worker = BatchSlideParseWorker()
        self.import_worker.parse_done.connect(self._updateParameters)
        self.import_worker.parse_done[str].connect(self._parseCancelled)

        self.worker = BatchCropWorker()
        self.worker.segmentation_finished.connect(self.setTableBarMax)
        self.worker.batch_progress.connect(self.updateTableProgressBars)
        self.worker.finished.connect(self.batchFinished)

    def folderClicked(self):
        folder = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        if folder:
            self.folder = folder
            self.ui.folder_edit.setText(folder)
            self._parseSlides(folder)

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
            thresholds = []
            seg_channels = []
            for row in rows:
                filename = row[0]
                input_paths.append(os.path.join(self.folder, filename))
                output_dirs.append(self.folder)
                seg_channel = row[3]
                seg_channels.append(seg_channel)
                thresholds.append(row[2][seg_channel])

            self._runBatch(input_paths, output_dirs, thresholds, seg_channels)    
        except:
            pass

    def stopClicked(self):
        if self.ui.stop_btn.isEnabled():
            if not self.worker.is_stopped():
                self.worker.stop()
                for bar in self.batch_table.bars:
                    bar.setValue(0)

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

    def _parseSlides(self, folder):
        if os.path.isdir(folder):
            count = 0
            for filename in os.listdir(folder):
                if filename.endswith('.ims'):
                    count += 1
            print(count)
            self.import_progress = Progress(self, count - 1, 'Slide import')
            self.import_worker.initialise(folder)
            self.import_worker.progress.connect(self.updateImportProgress)
            self.import_worker.finished.connect(self.importFinished)
            self.import_worker.start()

            if not self.import_progress.isVisible():          
                self.import_progress.show()

    def _parseCancelled(self):
        print("import didn't work")
        self.channels = ''
        self.thresholds = ''

    def _updateParameters(self, results):
        if results:
            channels = [str(c) for c in results[0]]
            thresholds = []
            for thresh in results[1]:
                thresholds.append(', '.join('{:.2f}'.format(t) for t in thresh))

            self.batch_table.update(self.folder, channels, thresholds)

    def _runBatch(self, input_paths, output_dirs, thresholds, seg_channels):
        self.worker.initialise(input_paths, output_dirs, seg_channels, thresholds)
        self.worker.start()