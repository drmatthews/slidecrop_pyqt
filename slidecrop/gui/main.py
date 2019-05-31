import os
import math

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import QtWebEngine
import numpy as np

from . import main_ui as UI
from .threshold import ThresholdDialog
from .batch import BatchDialog
from .progress import Progress
from .threads import (
    SlideImportWorker,
    SegmentationWorker,
    HistogramWorker,
    ThresholdWorker,
    OMEWorker,
    BatchCropWorker
)
from .roi import ROITable
from .roi import ROIItem
from ..ims.slide import SlideImage
from ..ims.deepzoom import DeepZoomGenerator


class SlideViewer(QtWidgets.QGraphicsView):
    """
    QGraphicsView for displaying and interacting with
    a low resolution representation of the slide to
    be segemented and cropped.
    """
    slideClicked = QtCore.pyqtSignal(QtCore.QPoint)

    def __init__(self, parent=None, widget=None, slide=None):
        super(SlideViewer, self).__init__(widget)
        self.parent = parent
        self.tabs = widget
        self._slide = slide
        self.tabs.setTabText(0, 'All')        
        self.viewport_geometry = (0, 20, 427, 561)
        self.setGeometry(*self.viewport_geometry)
        self._zoom = 0
        self._zl = 11
        self.max_zoom = 10
        if self._slide:
            self.max_zoom = self._slide.zoom_levels
        self.curr_img = None
        self.curr_level = 0
        self.factor = None
        self._empty = True
        self.initViewer()

    def initViewer(self):
        self._scene = QtWidgets.QGraphicsScene()
        self._image = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._image)
        self.setScene(self._scene)
        self._scene.newItem = None
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        sizePolicy = QtGui.QSizePolicy(
            QtGui.QSizePolicy.MinimumExpanding,
            QtGui.QSizePolicy.MinimumExpanding
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMinimumSize(QtCore.QSize(431, 541))

    def wheelEvent(self, event):
    
        if self.hasImage():
            if event.angleDelta().y() > 0:              
                factor = 1.25
                if self._zoom < self.max_zoom:
                    self._zoom += 1
                    self._zl += 1
            else:
                factor = 0.8
                self._zoom -= 1
                self._zl -= 1

            if self._zoom > 0 and self._zoom < self.max_zoom:
                self.scale(factor, factor)
            elif self._zoom == 0:
                self.fitInView()
            elif self._zoom < 0 or self._zoom > self.max_zoom:
                # print(self._zoom)
                self._zoom = 0

            a = self.mapToScene(
                QtCore.QPoint(0, 0)
            )                    
            b = self.mapToScene(
                QtCore.QPoint(
                    self.viewport().width(),
                    self.viewport().height()
                )
            )
            x = math.floor(a.x())
            y = math.floor(a.y())
            w = math.floor(b.x())
            h = math.floor(b.y())
            if x < 0:
                x = 0
            if y < 0:
                y = 0

            slide_level = self._slide.slide_level_for_zoom(self._zl)
            print(self._zoom)
            print(self._zl)
            print(slide_level)
            if slide_level != self.curr_level:
                factor = self._slide.get_level_downsample(slide_level)
                visible = [x, y, w, h]
                # visible = [v * 2 for v in visible]
                print(visible)
                self.updateImage(self._channel, self._threshold, region=visible)

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
        elif not self._image.pixmap().isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    @property
    def slide(self):
        return self._slide

    @slide.setter
    def slide(self, slide):
        self._slide = slide
        self._dz = DeepZoomGenerator(slide)
        self.max_zoom = self._dz.level_count

    def setMaxZoom(self, max_zoom):
        self.max_zoom = max_zoom

    def clear(self):
        self._empty = True
        self._zoom = 0
        self.factor = None
        self._scene.clear()
        self._clearTabs()
        self._image = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._image)        

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

    def hasImage(self):
        return not self._empty

    def fitInView(self, scale=True):
        rect = QtCore.QRectF(self._image.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasImage():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            # self._zoom = 0

    def setImage(self, qimg=None):
        pixmap = QtGui.QPixmap.fromImage(qimg)
        print('setImage called')
        self._empty = False
        self._image.setPixmap(pixmap)
        self.fitInView()

    def updateImage(self, channel, threshold, region=None, show_mask=True):
        """
        Updates the display of the low resolution slide image
        to show the result of any thresholding - probably
        needs refactoring (doing too many things).
        """
        print('update image')

        self._channel = channel
        self._threshold = threshold
        zlevel = self._zl
        slevel = self._slide.slide_level_for_zoom(zlevel)
        img = self._getPixelsFromSlide(slevel, region=region)

        _, h, w = img.shape
        img_RGB = np.zeros((h, w, 4), dtype=np.uint8)
        if isinstance(channel, int):
            color = self._slide.channel_colors[channel]
            img_RGB[:, :, 0] = img[channel, :, :] * color[0]
            img_RGB[:, :, 1] = img[channel, :, :] * color[1]
            img_RGB[:, :, 2] = img[channel, :, :] * color[2]
            img_RGB[:, :, 3] = 255
            if threshold and show_mask:
                thresh = threshold[channel]
                if 'bright' in self._slide.microscope_mode:
                    mask = img_RGB[:, :, channel] < thresh
                elif 'fluoro' in self._slide.microscope_mode:
                    mask = img_RGB[:, :, channel] > thresh
                img_RGB[mask, 0] = 255
                img_RGB[mask, 1] = 255
        else:
            img_RGB[:, :, 0] = img[0, :, :]
            img_RGB[:, :, 1] = img[1, :, :]
            img_RGB[:, :, 2] = img[2, :, :]
            img_RGB[:, :, 3] = 255
            if threshold and show_mask:
                thresh = threshold[0]
                print("rgb threshold {}".format(thresh))
                if 'bright' in self._slide.microscope_mode:
                    mask = img_RGB[:, :, 0] < thresh
                elif 'fluoro' in self._slide.microscope_mode:
                    mask = img_RGB[:, :, 0] > thresh
                img_RGB[mask, 0] = 255

        qimg = QtGui.QImage(img_RGB.data, w, h, QtGui.QImage.Format_RGBA8888)

        self.setImage(qimg)

    def updateDisplay(self, channel, threshold, region=None, show_mask=True):
        self._channel = channel
        self._threshold = threshold
        zlevel = self._zl
        slevel = self._slide.slide_level_for_zoom(zlevel)
        cols, rows = self._dz.level_tiles[zlevel]
        for row in range(rows):
            for col in range(cols):
                tile = self._dz.get_tile(slevel, (row, col))

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

    def updateTabs(self, channel_names):
        self._clearTabs()
        if len(channel_names) == 1:
            self.tabs.removeTab(0)

        for channel in channel_names:
            tab = QtWidgets.QWidget()
            self.tabs.addTab(tab, channel)

    def _getPixelsFromSlide(self, level, region=None):
        # only access the slide if really necessary -
        # if the zoom requires a change in resolution
        # level
        if level != self.curr_level:
            # region is hardwired for testing
            # region = [0, 0, 729, 1156]
            print(region)
            img = self._slide.read_multichannel_region(level, region=region)
        else:
            img = self.curr_img
        self.curr_img = img
        self.curr_level = level
        return img

    def _clearTabs(self):
        self.tabs.clear()
        self.tabs.insertTab(0, QtWidgets.QWidget(), 'All')        



class Window(QtWidgets.QMainWindow):
    """
    The main GUI window.
    """
    def __init__(self, filepath=None):
        super(Window, self).__init__()
        self.initUI()
        if filepath:
            self.importImage(filepath)

    def initUI(self):
        self.setAcceptDrops(True)
        self.ui = UI.Ui_MainWindow()
        self.ui.setupUi(self)

        # parameters
        self.slide_path = None
        self.slide = None
        self.basepath = ""
        self.curr_channel = None
        self.thresh_channel = 0
        self.curr_img = None
        self.slide_histogram = []
        self.threshold = []
        self.thresh_dialog = None
        self.batch_dialog = None
        self.rois = []
        self.scaled_regions = []

        # widgets
        self.viewer = SlideViewer(self, self.ui.slide_tabWidget)
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
            if self.slide:
                self.slide.close()
                self.viewer._slide.close()
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
            
            # if self.rois:
            #     # clear the viewer scene
            #     self.viewer.clearScene()

            #     # clear the roi table
            #     self.roi_table.clear()

            # set the channel to threshold
            channel = self.curr_channel
            if isinstance(channel, str):
                channel = 0
            
            # get the current threshold for that channel
            # determined using Otsu method
            threshold = self.threshold[channel]

            # get the histogram for that channel
            data = self.slide_histogram[channel]

            # open the threshold dialog
            self.thresh_dialog = ThresholdDialog(self)

            # plot the histogram
            self.thresh_dialog.updatePlot(threshold, data)

            # respond to changes in the threshold line
            thresh_line = self.thresh_dialog.thresh_line
            thresh_line.sigPositionChangeFinished.connect(self._lineMoved)

            if not self.thresh_dialog.isVisible():
                self.thresh_dialog.show()

            self.viewer.updateImage(self.curr_channel, self.threshold)

            # start the segmentation thread
            self.segmentation_worker = SegmentationWorker(
                self.slide_path, channel, threshold
            )

            # respond to the segmentation thread finishing
            self.segmentation_worker.segmentation_finished.connect(self.onSegmentationFinished)     
            self.segmentation_worker.start()            

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
        Responds to the importWorker thread.
        """
        self.slide_path = slide.filepath
        self.basepath = os.path.dirname(self.slide_path)
        self.basename = os.path.splitext(self.slide_path)[0]
        self.slide = slide
        self.viewer.slide = slide

        # set max zoom for viewer
        self.viewer.setMaxZoom(slide.zoom_levels)

        # get the microscope mode
        self.microscope_mode = self.slide.microscope_mode

        # get the channels in the slide
        self.channels = self.slide.channels()

        # determine otsu threshold
        self.thresh_worker.initialise(self.slide_path)
        self.thresh_worker.start()

        # get the histogram for each channel from the slide
        self.histogram_worker.initialise(self.slide_path)
        self.histogram_worker.start()

        # get channel names and colors
        self.channel_names = slide.channel_names
        self.channel_colors = slide.channel_colors

        # initialise the roi table
        self.roi_table.initTable()

        # update the image display tabs
        self.viewer.updateTabs(self.channel_names)

        # set current channel
        self.curr_channel = 'All'
        
        # set current image in display
        self.curr_img = self.slide.low_resolution_image()

        # update the display
        self.viewer.updateImage(self.curr_channel, self.threshold, show_mask=False)
        self.viewer.show()
        self.ui.slide_tabWidget.show()

        self.ui.roi_list.setGeometry(368, 9, 253, 582)


    def onImportCancelled(self, msg):
        pass

    def onChannelChange(self):
        """
        Responds to clicking on tabs
        """
        if self.curr_img is not None:
            idx = self.viewer.tabs.currentIndex() - 1
            show_mask = False
            channel = idx
            self.curr_channel = idx
            if idx < 0:
                self.curr_channel = 'All'
                channel = 0

            if self.thresh_dialog and self.thresh_dialog.isVisible():
                show_mask = True
                data = self.slide_histogram[channel]
                threshold = self.threshold[channel]
                self.thresh_dialog.updatePlot(threshold, data)
                thresh_line = self.thresh_dialog.thresh_line
                thresh_line.sigPositionChangeFinished.connect(self._lineMoved)                

            self.viewer.updateImage(self.curr_channel, self.threshold, show_mask=show_mask)

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
                roi = ROIItem(self, QtCore.QRectF(*r.roi))
                rois.append(roi)
                self.viewer.addROI(roi)

            self.rois = rois
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
    def _lineMoved(self, line):
        """
        Responds to the threshold line being moved
        on the thresh_dialog - sets new value for
        threshold.
        """
        if self.rois:
            self.viewer.clearScene()

        channel = self.curr_channel
        if isinstance(channel, str):
            channel = 0

        self.threshold[channel] = line.value()
        
        if (self.batch_dialog is not None and
            self.batch_dialog.isVisible()):
            print('line at {}'.format(line.value()))
            self.batch_dialog.batch_table.updateThresholdCell(self.threshold)

        self.viewer.updateImage(self.curr_channel, self.threshold)

        # start the segmentation thread
        self.segmentation_worker = SegmentationWorker(
            self.slide_path, channel, line.value()
        )

        # respond to the segmentation thread finishing
        self.segmentation_worker.segmentation_finished.connect(self.onSegmentationFinished)     
        self.segmentation_worker.start()
        

if __name__ == '__main__':

    import sys
    app = QtWidgets.QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit( app.exec_() )
