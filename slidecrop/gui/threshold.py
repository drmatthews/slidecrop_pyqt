import os

from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

from numpy import arange, max, nonzero

import slidecrop.gui.threshold_ui as thresh_UI
from slidecrop.gui.threads import ThresholdWorker


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

        # the following is probably changing the size policy
        # preventing the graph being resized

        # TODO set size and figure out how to allow resizing
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

        self.thresh_worker = ThresholdWorker()
        self.thresh_worker.threshold_finished.connect(self.updateHistogramAndDisplay)

        # set the combo box to 'otsu'
        self.ui.method_combo.setCurrentIndex(2)
        self.ui.method_combo.currentIndexChanged.connect(self.onMethodChange)
        self.histogram = HistogramGraph(self.ui.histogram_widget, data, threshold)

    def onMethodChange(self, val):
        print('method change called')
        method = self.ui.method_combo.currentText().lower()
        self.thresh_worker.initialise(self.parent.slide_path, method)
        # lauch a threshold worker to recalculate the
        # channel thresholds
        self.thresh_worker.start()

    def updateHistogramAndDisplay(self, result):
        # update the graph - line position
        self.histogram.threshold = result
        self.histogram.plot()
        # new threshold line is created so 
        # force update of display
        # note that this should probably be done
        # by emitting a signal
        channel = self.parent.curr_channel
        if isinstance(channel, str):
            channel = 0
        self.parent.threshold[channel] = result[channel]
        self.parent._updateDisplayImage(self.parent.curr_channel)    

    def closeEvent(self, event):
        dchannel = self.parent.curr_channel
        # update display - should probably emit a signal
        self.parent._updateDisplayImage(dchannel, show_mask=False)