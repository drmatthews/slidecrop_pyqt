import os
import traceback
import sys
import time

from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, QRunnable, QObject
from PyQt5.QtCore import pyqtSignal, pyqtSlot

import numpy as np

from slidecrop.utils.otsu import threshold_otsu
from slidecrop.ims.slide import SlideImage
from slidecrop.processing.segmentation import SegmentSlide
from slidecrop.ome.ome_tiff_generator import OMETiffGenerator
from slidecrop.processing.crop import CropSlide


# need to move over to this to tidy up threading
# to do this move stuff that is currently in "run()"
# methods to functions which can be passed to the
# worker instance
class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super().__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done



class BaseWorker(QThread):
    """
    Base class for worker threads. Is itself a subclass
    of Qt QThread class.
    """
    def __init__(self):
        QThread.__init__(self)
        self.stopped = False

    def __del__(self):
        self.wait()

    def stop(self):
        self.stopped = True

    def is_stopped(self):
        return self.stopped

    def run(self):
        """
        Subclasses should reimplement this
        """
        pass


class SlideImportWorker(BaseWorker):
    """
    Thread for importing (reading) a *.ims file
    """
    import_done = pyqtSignal([SlideImage], [str])

    def __init__(self, slide_path=None):
        """
        Constructor

        :param slide_path: path to slide image in *.ims format
        :type slide_path: str
        """
        super().__init__()
        self.slide_path = slide_path

    def run(self):
        """
        Called when the start() method is called on the instance

        Emits the SlideImage instance
        """
        try:
            slide = SlideImage(self.slide_path)
            self.import_done.emit(slide)
        except:
            self.import_done[str].emit('')


class BatchSlideParseWorker(BaseWorker):
    """
    Thread for batch parsing (reading) a *.ims file
    to get thresholds and channels
    """
    progress = pyqtSignal(int)
    parse_done = pyqtSignal([object], [str])

    def __init__(self, folder=None):
        """
        Constructor

        :param slide_path: path to slide image in *.ims format
        :type slide_path: str
        """
        super().__init__()
        self.folder = folder

    def initialise(self, folder):
        self.folder = folder

    def _getThreshold(self, slide):
        size_c = slide.size_c
        thresh = []
        for c in range(size_c):
            hist = slide.get_histogram(c=c)
            thresh.append(threshold_otsu(hist))        

        return thresh

    def run(self):
        """
        Called when the start() method is called on the instance

        Emits tuple of channels (int) and thresholds (list)
        """
        try:
            channels = []
            thresholds = []
            count = 0
            for filename in os.listdir(self.folder):
                if filename.endswith('.ims'):
                    slide_path = os.path.join(self.folder, filename)
                    slide = SlideImage(slide_path)
                    channels.append(slide.size_c)
                    thresholds.append(self._getThreshold(slide))
                    slide.close()
                    self.progress.emit(count)
                    time.sleep(0.2)
                    count += 1
            print(count)
            self.parse_done.emit((channels, thresholds))
        except:
            self.parse_done[str].emit("")


class SegmentationWorker(BaseWorker):
    """
    Thread for segmenting a SlideImage
    """
    segmentation_finished = pyqtSignal(list)

    def __init__(self, slide_path=None, channel=None, threshold=None):
        """
        Constructor

        :param slide_path: path to slide image in *.ims format
        :type slide_path: str
        :param channel: channel to segment
        :type channel: int
        :param threshold: pixel intensity value to use as threshold
        :type threshold: float
        """
        super().__init__()
        self.slide_path = slide_path
        self.channel = channel
        self.threshold = threshold

    def run(self):
        """
        Called when the start() method is called on the instance

        Emits the regions segmented
        """
        try:
            with SlideImage(self.slide_path) as slide:
                mode = slide.microscope_mode
                lo = slide.low_resolution_image()
                factor = slide.scale_factor

            segmenter = SegmentSlide(
                mode, factor, channel=self.channel,
                thresh_method='manual', threshold=self.threshold
            )
            self.segmentation_finished.emit(segmenter.run(lo))
        except:
            pass


class ThresholdWorker(BaseWorker):
    """
    Thread for finding Otsu threshold for each channel
    in a SlideImage
    """
    threshold_finished = pyqtSignal(list)

    def __init__(self, slide_path=None, method='auto'):
        """
        Constructor

        :param slide_path: path to slide image in *.ims format
        :type slide_path: str        
        """
        super().__init__()
        self.slide_path = slide_path

    def run(self):
        """
        Called when the start() method is called on the instance

        Emits a list of Otsu determined threshold levels
        """
        try:
            with SlideImage(self.slide_path) as slide:
                size_c = slide.size_c
                thresh = []
                for c in range(size_c):
                    hist = slide.get_histogram(c=c)
                    thresh.append(threshold_otsu(hist))

            self.threshold_finished.emit(thresh)
        except:
            pass


class HistogramWorker(BaseWorker):
    """
    Thread for getting image histograms from *.ims image
    metadata
    """
    histogram_finished = pyqtSignal(list)

    def __init__(self, slide_path=None):
        """
        Constructor

        :param slide_path: path to slide image in *.ims format
        :type slide_path: str    
        """        
        super().__init__()
        self.slide_path = slide_path

    def run(self):
        """
        Called when the start() method is called on the instance

        Emits list of image histograms as numpy arrays
        """
        with SlideImage(self.slide_path) as slide:
            y = []
            for c in range(slide.size_c):
                y.append(slide.get_histogram(c=c))

        self.histogram_finished.emit(y)


class OMEWorker(BaseWorker):
    """
    Thread for creating *.ome.tif images from pixel regions
    extracted from *.ims images
    """
    progress = pyqtSignal(int)

    def __init__(self, slide_path, outputdir, channels, regions):
        """
        Constructor

        :param slide_path: path to slide image in *.ims format
        :type slide_path: str
        :param outputdir: directory where *.ome.tiff will be saved
        :type outputdir: str
        :param channels: the channels to be written
        :type channels: list or int
        :param regions: x, y, w, h of regions to be written
        :type regions: list
        """
        super().__init__()
        self.slide_path = slide_path
        self.outputdir = outputdir
        self.channels = channels
        self.regions = regions

    def run(self):
        """
        Called when the start() method is called on the instance

        Emits a int indicating which region is being written
        to *.ome.tiff
        """
        if self.regions:
            try:
                with SlideImage(self.slide_path) as slide:
                    for rid, region in enumerate(self.regions):

                        filename = slide.basename + '_section_{}.ome.tif'.format(rid)
                        ometiff = OMETiffGenerator(
                            slide,
                            filename,
                            self.outputdir,
                            self.channels, 0, 0
                        )
                        self.progress.emit(rid)
                        ometiff.run(region)
            except:
                pass


class BatchSegmentationWorker(BaseWorker):
    """
    Thread for segmenting a SlideImage
    """
    segmentation_finished = pyqtSignal(list)

    def __init__(self, input_paths=None, channels=None, thresholds=None):
        """
        Constructor

        :param input_paths: paths to slide images in *.ims format
        :type slide_path: str
        :param channels: channel to segment
        :type channels: list of int
        :param threshold: pixel intensity value to use as threshold
        :type threshold: float
        """
        super().__init__()
        self.input_paths = input_paths
        self.channels = channels
        self.thresholds = thresholds

    def run(self):
        """
        Called when the start() method is called on the instance

        Emits the regions segmented
        """
        try:
            batch_regions = []
            for sid, slide_path in enumerate(self.input_paths):
                seg_channel = self.channels[sid]
                threshold = self.thresholds[sid]
                with SlideImage(slide_path) as slide:
                    mode = slide.microscope_mode
                    lo = slide.low_resolution_image()
                    factor = slide.scale_factor

                    segmenter = SegmentSlide(
                        mode, factor, channel=seg_channel,
                        thresh_method='manual', threshold=threshold
                    )
                    batch_regions.append(segmenter.run(lo))
            self.segmentation_finished.emit(batch_regions)
        except:
            pass


class BatchCropWorker(BaseWorker):
    """
    Thread for creating *.ome.tif images from pixel regions
    extracted from *.ims images
    """
    segmentation_finished = pyqtSignal(object)
    batch_progress = pyqtSignal(object)

    def __init__(self, input_paths=None, output_dirs=None, seg_channels=None, thresholds=None):
        """
        Constructor

        :param input_paths: folder containing *.ims images
        :type input_paths: str
        :param output_dirs: directory where *.ome.tiff will be saved
        :type output_dirs: str
        :param regions: pixel regions to be cropped
        :param regions: list
        """
        super().__init__()
        self.input_paths = input_paths
        self.output_dirs = output_dirs
        self.channels = seg_channels
        self.thresholds = thresholds

    def initialise(self, input_paths, output_dirs, seg_channels, thresholds):
        self.stopped = False
        self.input_paths = input_paths
        self.output_dirs = output_dirs
        self.channels = seg_channels
        self.thresholds = thresholds

    def run(self):
        """
        Called when the start() method is called on the instance

        Emits a int indicating which region is being written
        to *.ome.tiff
        """
        tic = time.time()
        count = 0
        print(self.is_stopped())
        while not self.is_stopped():
            for sid, slide_path in enumerate(self.input_paths):
                seg_channel = self.channels[sid]
                threshold = self.thresholds[sid]

                with SlideImage(slide_path) as slide:
                    mode = slide.microscope_mode
                    lo = slide.low_resolution_image()
                    factor = slide.scale_factor

                    segmenter = SegmentSlide(
                        mode, factor, channel=seg_channel,
                        thresh_method='manual', threshold=threshold
                    )
                    regions = segmenter.run(lo)
                    self.segmentation_finished.emit((sid, len(regions)))

                    for rid, region in enumerate(regions):
                        filename = slide.basename + '_section_{}.ome.tif'.format(rid)
                        print('writing filename {}'.format(filename))
                        channels = [c for c in range(slide.size_c)]
                        ometiff = OMETiffGenerator(
                            slide,
                            filename,
                            self.output_dirs[sid],
                            channels, 0, 0
                        )
                        self.batch_progress.emit((sid, rid))
                        ometiff.run(region)
                        count += 1
            self.stopped = True
        toc = time.time()
        print(toc - tic)
