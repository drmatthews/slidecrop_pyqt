import os

from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

from numpy import arange, max, nonzero

from . import threshold_ui as thresh_UI
from .threads import ThresholdWorker


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


class ThresholdDialog(QtWidgets.QDialog):
    pg.setConfigOptions(antialias=True)
    pg.setConfigOption('background', (240, 240, 240))
    pg.setConfigOption('foreground', 'k')

    def __init__(self, parent=None, data=None, threshold=None, **kargs):
        super(ThresholdDialog, self).__init__(parent=parent)
        self.parent = parent
        self.data = data
        self.threshold = threshold
        self.thresh_line = None
        self.ui = thresh_UI.Ui_ThresholdDialog()
        self.ui.setupUi(self)

        # set the combo box to 'otsu'
        self.ui.method_combo.setCurrentIndex(2)
        self.ui.method_combo.currentIndexChanged.connect(self.onMethodChange) 

        self.thresh_worker = ThresholdWorker()
        self.thresh_worker.threshold_finished.connect(self.updateLineAndDisplay)               

        grad = QtGui.QLinearGradient(0, 0, 0, 3)
        grad.setColorAt(0.1, pg.mkColor('#000000'))
        grad.setColorAt(0.9, pg.mkColor((156, 220, 218)))
        self.fillbrush = (30, 30, 30)
        self.linepen = (200, 200, 100)

    def updateLine(self, line_pos):
        if self.thresh_line:
            # self.plot.removeItem(self.thresh_line)
            # self.thresh_line = ThresholdLine(line_pos)
            # self.plot.addItem(self.thresh_line)

            self.thresh_line.setValue(line_pos)

    def updatePlot(self, line_pos, ydata):

        xdata = arange(256)
        ydata = ydata[nonzero(ydata)]
        xdata = xdata[nonzero(ydata)]
        ymax = max(ydata)

        self.ui.histogram_widget.clear()
        p = self.ui.histogram_widget.addPlot()
        p.setMenuEnabled(False)
        p.setMouseEnabled(x=False, y=False)
        p.hideAxis('left')
        p.hideAxis('bottom')
        
        p.plot(
            x=xdata, y=ydata,
            pen=self.linepen,
            brush=self.fillbrush,
            fillLevel=0
        )

        p.setXRange(0, 255, padding=0)
        p.setYRange(1, ymax, padding=0)
        p.setLimits(xMin=0, xMax=255, yMin=1, yMax=ymax)
        p.setLogMode(False, True)

        if self.thresh_line is not None:
            p.removeItem(self.thresh_line)
            print('line removed')

        self.thresh_line = ThresholdLine(line_pos)
        p.addItem(self.thresh_line)
        self.plot = p

    def onMethodChange(self, val):
        print('method change called')
        method = self.ui.method_combo.currentText().lower()

        # keep batch dialog in sync
        bd = self.parent.batch_dialog
        if bd is not None and bd.isVisible():
            self.parent.batch_dialog.batch_table.updateThreshMethodCell(val)
        
        self.thresh_worker.initialise(self.parent.slide_path, method)
        # lauch a threshold worker to recalculate the
        # channel thresholds
        self.thresh_worker.start()

    def updateLineAndDisplay(self, result):
        print("result")
        curr_channel = self.parent.curr_channel
        if isinstance(curr_channel, str):
            curr_channel = 0

        threshold = result[curr_channel]
        data = self.parent.slide_histogram[curr_channel]
        print(data.shape)
        self.updateLine(threshold)
        # new threshold line is created so 
        # force update of display
        # note that this should probably be done
        # by emitting a signal
        channel = self.parent.curr_channel
        if isinstance(channel, str):
            channel = 0
        self.parent.threshold = result
        self.parent._updateDisplayImage(self.parent.curr_channel)

    def closeEvent(self, event):
        dchannel = self.parent.curr_channel

        # if there were rois on the viewer, put them back
        if self.parent.rois:

            for roi in self.parent.rois:
                self.parent.viewer.addROI(roi)

            self.parent.roi_table.update(self.parent.rois)

        # update display - should probably emit a signal
        self.parent._updateDisplayImage(dchannel, show_mask=False)

