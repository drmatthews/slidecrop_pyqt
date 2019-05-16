import os

from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np

import slidecrop.gui.main_ui as UI
from slidecrop.gui.threshold import ThresholdDialog
from slidecrop.gui.batch import BatchDialog
from slidecrop.gui.progress import Progress
from slidecrop.ims.slide import SlideImage
from slidecrop.gui.threads import (
    SlideImportWorker,
    SegmentationWorker,
    HistogramWorker,
    ThresholdWorker,
    OMEWorker,
    BatchCropWorker
)
from slidecrop.gui.roi import ROITable
from slidecrop.gui.roi import ROIItem


class SlideViewer(QtWidgets.QGraphicsView):
    """
    QGraphicsView for displaying and interacting with
    a low resolution representation of the slide to
    be segemented and cropped.
    """
    slideClicked = QtCore.pyqtSignal(QtCore.QPoint)

    def __init__(self, parent=None, widget=None):
        super(SlideViewer, self).__init__(widget)
        self.parent = parent
        self.viewport_geometry = (0, 20, 427, 561)
        self.setGeometry(*self.viewport_geometry)
        self._zoom = 0
        self.factor = None
        self._empty = True
        self._scene = QtWidgets.QGraphicsScene()
        self._slide = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._slide)
        self.setScene(self._scene)
        self._scene.newItem = None
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

        sizePolicy = QtGui.QSizePolicy(
            QtGui.QSizePolicy.MinimumExpanding,
            QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QtCore.QSize(431, 541))        

    def clearScene(self):
        """
        Remove all ROIItems from the scene
        """
        for item in self._scene.items():
            if not isinstance(item, QtWidgets.QGraphicsPixmapItem):
                self._scene.removeItem(item)

    def deselectROIs(self):
        for item in self._scene.items():
            if not isinstance(item, QtWidgets.QGraphicsPixmapItem):
                item.setSelected(False)      

    def hasSlide(self):
        return not self._empty

    def fitInView(self, scale=True):
        rect = QtCore.QRectF(self._slide.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasSlide() and self._zoom == 0:
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            # self._zoom = 0

    def setSlide(self, qimg=None):
        pixmap = QtGui.QPixmap.fromImage(qimg)
        if not pixmap.isNull():
            self._empty = False
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self._slide.setPixmap(pixmap)
        else:
            self._empty = True
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self._slide.setPixmap(QtGui.QPixmap())
        self.fitInView()

    def wheelEvent(self, event):
    
        if self.hasSlide():
            if event.angleDelta().y() > 0:              
                factor = 1.25
                self._zoom += 1
            else:
                factor = 0.8
                self._zoom -= 1
            if self._zoom > 0:
                self.scale(factor, factor)
            elif self._zoom == 0:
                self.fitInView()
            else:
                self._zoom = 0

    def keyPressEvent(self, event):
        """
        Detect when the delete key is pressed - will
        delete any ROIItem that is underneath the mouse.
        """
        # determine what key is pressed
        if event.key() == QtCore.Qt.Key_Delete:
            # if it is delete, remove the selected items
            items = self._scene.selectedItems()
            for item in items:
                if not isinstance(item, QtWidgets.QGraphicsPixmapItem):
                    self._scene.removeItem(item)

            # make a list of the remaining items
            remaining = self._scene.items()
            roi_list = []
            for item in remaining:
                if not isinstance(item, QtWidgets.QGraphicsPixmapItem):
                    roi_list.append(item)

            # redraw the roi_table with the remaining items
            self.parent.roi_table.update(roi_list)

    def dragEnterEvent(self, event):
        """
        Overrides built-in dragEnterEvent.
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """
        Overrides built-in dragMoveEvent.
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
 
    def dropEvent(self, event):
        """
        Overrides built-in dropEvent.
        """
        url = event.mimeData().urls()[0]
        path = url.toLocalFile()
        if os.path.isfile(path):
            self.parent.importImage(path)
        elif os.path.isdir(path):
            self.parent.batch_dialog = BatchDialog(self.parent, path)

            if not self.parent.batch_dialog.isVisible():          
                self.parent.batch_dialog.show()

    def toggleDragMode(self):
        if self.dragMode() == QtWidgets.QGraphicsView.ScrollHandDrag:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        elif not self._slide.pixmap().isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def addROI(self, roi):
        """
        Add an ROIItem to the scene.
        """
        self._scene.newItem = roi
        self._scene.newItem.setRect(roi.rect())
        self._scene.addItem(self._scene.newItem)

    def roi_number(self):
        """
        Return the current number of ROIItems in the scene.
        """
        regions = []
        for item in self._scene.items():
            if not isinstance(item, QtWidgets.QGraphicsPixmapItem):
                regions.append(item)
        return len(regions)


class Window(QtWidgets.QMainWindow):
    """
    The main GUI window.
    """
    def __init__(self):
        super(Window, self).__init__()
        self.initUI()

    def initUI(self):
        self.setAcceptDrops(True)
        self.ui = UI.Ui_MainWindow()
        self.ui.setupUi(self)

        # parameters
        self.slide_path = None
        self.basepath = ""
        self.curr_channel = None
        self.thresh_channel = 0
        self.curr_img = None
        self.slide_histogram = []
        self.threshold = []
        self.thresh_dialog = None
        self.scaled_regions = []

        # widgets
        self.viewer = SlideViewer(self, self.ui.slide_tabWidget)
        self.ui.slide_tabWidget.setTabText(0, 'All')
        self.roi_table = ROITable(self, self.ui.roi_list)

        # signals
        self.ui.actionOpen.triggered.connect(self.openClicked)
        self.ui.actionExit.triggered.connect(self.closeEvent)
        self.ui.actionSegment.triggered.connect(self.segmentClicked)
        self.ui.actionCrop.triggered.connect(self.cropClicked)
        self.ui.actionThreshold.triggered.connect(self.thresholdClicked)
        self.ui.actionBatch.triggered.connect(self.batchClicked)        
        self.ui.slide_tabWidget.currentChanged.connect(self.onChannelChange)
        
        # threads
        self.import_worker = SlideImportWorker()
        self.import_worker.import_done.connect(self.onImportFinished)
        self.import_worker.import_done[str].connect(self.onImportCancelled)        
        self.histogram_worker = HistogramWorker()
        self.histogram_worker.histogram_finished.connect(self.onHistogramFinished)
        self.thresh_worker = ThresholdWorker()
        self.thresh_worker.threshold_finished.connect(self.onThresholdFinished)

    # events
    def dragEnterEvent(self, event):
        """
        Overrides built-in dragEnterEvent.
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """
        Overrides built-in dragMoveEvent.
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
 
    def dropEvent(self, event):
        """
        Overrides built-in dropEvent.
        """
        url = event.mimeData().urls()[0]
        path = url.toLocalFile()
        if os.path.isfile(path):
            self.importImage(path)
        elif os.path.isdir(path):
            self.batch_dialog = BatchDialog(self, path)

            if not self.batch_dialog.isVisible():          
                self.batch_dialog.show()

    def closeEvent(self, event):
        """
        Overrides built-in closeEvent
        """
        result = QtWidgets.QMessageBox.question(self,
                      "Confirm Exit...",
                      "Are you sure you want to exit ?",
                      QtWidgets.QMessageBox.Yes| QtWidgets.QMessageBox.No)
        event.ignore()

        if result == QtWidgets.QMessageBox.Yes:
            event.accept()

    # actions
    def openClicked(self):
        """
        openAction clicked. Uses the _importImage method to 
        start the import_worker thread.
        """
        filepath = (
            QtWidgets.QFileDialog.getOpenFileName(self,
                "Load Slide", self.basepath, "*.ims")
        )
        self.importImage(filepath[0])

    def importImage(self, filepath):
        if filepath:
            self.viewer.clearScene()
            self.import_worker.slide_path = filepath
            self.import_worker.start()

    def thresholdClicked(self):
        """
        thresholdAction clicked. Opens the threshold dialog.
        """
        if self.curr_img is not None and self.slide_histogram:
            self._updateDisplayImage(self.curr_channel)

            # set the channel to threshold
            channel = self.curr_channel
            if isinstance(channel, str):
                channel = 0
            
            # get the current threshold for that channel
            # determined using Otsu method
            threshold = self.threshold[channel]

            # get the histogram for that channel
            histogram = self.slide_histogram[channel]

            # open the threshold dialog
            self.thresh_dialog = ThresholdDialog(
                self, histogram, threshold
            )

            # plot the histogram
            self.thresh_dialog.histogram.plot()

            # respond to changes in the threshold line
            thresh_line = self.thresh_dialog.histogram.thresh_line
            thresh_line.sigPositionChangeFinished.connect(self._lineMoved)

            if not self.thresh_dialog.isVisible():          
                self.thresh_dialog.show()

    def segmentClicked(self):
        """
        segmentAction clicked. Activates the 
        segmentation_worker thread.
        """
        if self.curr_img is not None:

            self.viewer.clearScene()

            # determine the channel to segment
            segment_channel = self.curr_channel
            if isinstance(segment_channel, str):
                segment_channel = 0

            # get the current threshold for that channel
            threshold = self.threshold[segment_channel]

            # start the segmentation thread
            self.segmentation_worker = SegmentationWorker(
                self.slide_path, segment_channel, threshold
            )

            # respond to the segmentation thread finishing
            self.segmentation_worker.segmentation_finished.connect(self.onSegmentationFinished)     
            self.segmentation_worker.start()


    def cropClicked(self):
        """
        cropAction clicked. Activates the OMEWorker thread.
        """
        # get the ids of the regions to be cropped
        # these will have checkboxes checked
        rids = self.roi_table.get_checked_rows()

        # if there is an image displayed and there are regions
        # to be cropped
        if self.curr_img is not None and rids:

            # get the actual scaled regions to be cropped
            # these are instances of the Segmentation class
            regions = [self.scaled_regions[r] for r in rids]
            num_regions = len(regions)

            if num_regions > 0:
                # set up the progress bar
                self.progress_dialog = Progress(self, num_regions - 1, 'Crop')
                # explitily set outputdir and channels while testing
                outputdir = os.path.dirname(self.slide_path)
                channels = [c for c in range(self.channels)]

                # start the OMEWorker thread
                self.ome_worker = OMEWorker(self.slide_path, outputdir, channels, regions)
                self.ome_worker.start()

                # respond to the progress signal
                self.ome_worker.progress.connect(self.updateProgress)

                # respond to the finished signal
                self.ome_worker.finished.connect(self.onCropFinished)
                if not self.progress_dialog.isVisible():          
                    self.progress_dialog.show()


    def batchClicked(self):
        self.batch_dialog = BatchDialog(self)

        if not self.batch_dialog.isVisible():          
            self.batch_dialog.show()


    # slots
    def onImportFinished(self, slide):
        """
        Responds the importWorker thread.
        """
        self.slide_path = slide.filepath
        self.basepath = os.path.dirname(self.slide_path)
        self.basename = os.path.splitext(self.slide_path)[0]
        self.slide = slide

        # get the microscope mode
        self.microscope_mode = self.slide.microscope_mode

        # get the channels in the slide
        self.channels = self.slide.channels()

        # determine otsu threshold
        self.thresh_worker.slide_path = self.slide_path
        self.thresh_worker.start()

        # get the histogram for each channel from the slide
        self.histogram_worker.slide_path = self.slide_path
        self.histogram_worker.start()        

        # get channel names and colors
        self.channel_names = slide.channel_names
        self.channel_colors = slide.channel_colors

        # initialise the roi table
        self.roi_table.initTable()

        # update the image display tabs
        self.ui.slide_tabWidget.clear()
        self.ui.slide_tabWidget.insertTab(0, QtWidgets.QWidget(), 'All')
        if slide.size_c == 1:
            self.ui.slide_tabWidget.removeTab(0)

        for channel in range(slide.size_c):
            tab = QtWidgets.QWidget()
            self.ui.slide_tabWidget.addTab(tab, self.channel_names[channel])

        # set current channel
        self.curr_channel = 'All'
        
        # set current image in display
        self.curr_img = self.slide.low_resolution_image()

        # update the display
        self._updateDisplayImage(self.curr_channel, show_mask=False)
        self.viewer.show()
        self.ui.slide_tabWidget.show()

        self.ui.roi_list.setGeometry(368, 9, 253, 582)
        # close the hdf file
        self.slide.close()

    def onImportCancelled(self, msg):
        pass

    def onChannelChange(self):
        """
        Responds to clicking on tabs
        """
        idx = self.ui.slide_tabWidget.currentIndex() - 1
        if self.curr_img is not None:
            show_mask = False
            channel = idx
            self.curr_channel = idx
            if idx < 0:
                self.curr_channel = 'All'
                channel = 0

            if self.thresh_dialog and self.thresh_dialog.isVisible():
                show_mask = True
                self.thresh_dialog.histogram.data = self.slide_histogram[channel]
                self.thresh_dialog.histogram.threshold = self.threshold[channel]
                self.thresh_dialog.histogram.plot()
                thresh_line = self.thresh_dialog.histogram.thresh_line
                thresh_line.sigPositionChangeFinished.connect(self._lineMoved)                

            self._updateDisplayImage(self.curr_channel, show_mask=show_mask)

    def onThresholdFinished(self, result):
        if result:
            self.threshold = result

    def onSegmentationFinished(self, result):
        """
        Update the ROI table, check every row
        and store the scaled regions produced
        by segmentation in self.scaled_regions.
        """
        if result:
            rois = []
            for r in result:
                roi = ROIItem(self.parent, QtCore.QRectF(*r.roi))
                rois.append(roi)
                self.viewer.addROI(roi)

            self.roi_table.update(rois)
            self.scaled_regions = result

    def onHistogramFinished(self, result):
        if result:
            self.slide_histogram = result

    def updateProgress(self, value):
        if self.progress_dialog.isVisible():
            self.progress_dialog.updateBar(value)

    def onCropFinished(self):
        if self.progress_dialog.isVisible():
            self.progress_dialog.close()

    # helpers
    def _updateDisplayImage(self, channel, show_mask=True):
        """
        Updates the display of the low resolution slide image
        to show the result of any thresholding - probably
        needs refactoring (doing too many things).
        """
        # image is being split for RGB for testing only
        # finally only 'All' tab will be displayed
        print("curr_channel {}".format(self.curr_channel))
        print("threshold {}".format(self.threshold))

        img = self.curr_img
        _, h, w = img.shape
        img_RGB = np.zeros((h, w, 4), dtype=np.uint8)
        if isinstance(channel, int):
            color = self.channel_colors[channel]
            img_RGB[:, :, 0] = img[channel, :, :] * color[0]
            img_RGB[:, :, 1] = img[channel, :, :] * color[1]
            img_RGB[:, :, 2] = img[channel, :, :] * color[2]
            img_RGB[:, :, 3] = 255
            if self.threshold and show_mask:
                threshold = self.threshold[channel]
                if 'bright' in self.microscope_mode:
                    mask = img_RGB[:, :, channel] < threshold
                elif 'fluoro' in self.microscope_mode:
                    mask = img_RGB[:, :, channel] > threshold
                img_RGB[mask, 0] = 255
                img_RGB[mask, 1] = 255
        else:
            img_RGB[:, :, 0] = img[0, :, :]
            img_RGB[:, :, 1] = img[1, :, :]
            img_RGB[:, :, 2] = img[2, :, :]
            img_RGB[:, :, 3] = 255
            if self.threshold and show_mask:
                threshold = self.threshold[0]
                print("rgb threshold {}".format(threshold))
                if 'bright' in self.microscope_mode:
                    mask = img_RGB[:, :, 0] < threshold
                elif 'fluoro' in self.microscope_mode:
                    mask = img_RGB[:, :, 0] > threshold
                img_RGB[mask, 0] = 255

        qimg = QtGui.QImage(img_RGB.data, w, h, QtGui.QImage.Format_RGBA8888)

        self.viewer.setSlide(qimg)     

    def _lineMoved(self, line):
        """
        Responds to the threshold line being moved
        on the thresh_dialog - sets new value for
        threshold.
        """
        channel = self.curr_channel
        if isinstance(channel, str):
            channel = 0
        print(line.value())
        self.threshold[channel] = line.value()
        self._updateDisplayImage(self.curr_channel)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit( app.exec_() )
