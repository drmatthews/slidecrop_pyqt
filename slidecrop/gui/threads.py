import os
import traceback
import sys
import time

from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread, QRunnable, QObject
from PyQt5.QtCore import pyqtSignal, pyqtSlot

import numpy as np
from skimage.filters import (
    threshold_isodata,
    threshold_mean,
    threshold_otsu,
    threshold_triangle,
    threshold_yen
)

# from slidecrop.processing.otsu import threshold_otsu
from ..ims.slide import SlideImage
from ..processing.crop import CropSlide
from ..processing.segmentation import Segment
from ..ome.ometiff import OMETiffGenerator


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
        `object` indicating % progress (will be `int` or `tuple`)

    custom_callback
        `object` any other type of signal (e.g. partial results)

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(object)
    custom_callback = pyqtSignal(object)


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
        self.kwargs['custom_callback'] = self.signals.custom_callback        

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

#####
# functions to run in threads
def _import(slide_path,
            progress_callback=None,
            custom_callback=None):

    slide = SlideImage(slide_path)
    threshold = _get_threshold(slide, 'otsu')
    hist = []
    for c in range(slide.size_c):
        hist.append(slide.get_histogram(c=c))
    return (slide, threshold, hist)


def _batch_import(folder, thresh_method,
                  progress_callback=None,
                  custom_callback=None):

    channels = []
    thresholds = []
    count = 0
    for filename in os.listdir(folder):
        if filename.endswith('.ims'):
            slide_path = os.path.join(folder, filename)

            with SlideImage(slide_path) as slide:
                channels.append(slide.size_c)
                thresholds.append(_get_threshold(slide, thresh_method))

            progress_callback.emit(count)
            time.sleep(0.2)
            count += 1    

    return (channels, thresholds)

def _get_histogram(slide,
                   progress_callback=None,
                   custom_callback=None):

    y = []
    for c in range(slide.size_c):
        y.append(slide.get_histogram(c=c))
    return y


def _auto_threshold(plane, method):
    if 'isodata' in method:
        thresh = threshold_isodata(plane)        
    elif 'mean' in method:
        thresh = threshold_mean(plane)
    elif 'otsu' in method:
        thresh = threshold_otsu(plane)
    elif 'triangle' in method:
        thresh = threshold_triangle(plane)
    elif 'yen' in method:
        thresh = threshold_yen(plane)
    else:
        raise NotImplementedError('thresholding method not supported')
    return thresh       


def _get_threshold(slide, method,
                   progress_callback=None,
                   custom_callback=None):

    low = slide.low_resolution_image()
    size_c = slide.size_c
    thresh = []
    for c in range(size_c):
        plane = low[c, :, :]  
        thresh.append(_auto_threshold(plane, method))       

    return thresh


def _threshold(slide_path, method,
               progress_callback=None,
               custom_callback=None):

    with SlideImage(slide_path) as slide:
        threshold = _get_threshold(slide, method)

    return threshold


def _segment(slide_path,
             channel, threshold,
             progress_callback=None,
             custom_callback=None):

    with SlideImage(slide_path) as slide:
        mode = slide.microscope_mode
        lo = slide.low_resolution_image()
        factor = slide.scale_factor

        segmenter = Segment(
            mode, factor, channel=channel,
            thresh_method='manual', threshold=threshold
        )
        regions = segmenter.run(lo)
    return regions


def _make_ome(slide, outputdir, region, rid):
    filename = slide.basename + '_section_{}.ome.tif'.format(rid)    
    channels = [c for c in range(slide.size_c)]    
    ometiff = OMETiffGenerator(
        slide,
        filename,
        outputdir,
        channels, 0, 0
    )
    ometiff.run(region)


def _crop_regions(slide_path,
                  outputdir, regions,
                  progress_callback=None,
                  custom_callback=None):

    with SlideImage(slide_path) as slide:
        for rid, region in enumerate(regions):
            _make_ome(slide, outputdir, region, rid)
            time.sleep(0.1)
            progress_callback.emit(rid)


def _batch_crop(input_paths, output_dirs, channels,
                thresholds, progress_callback=None,
                custom_callback=None):

    count = 0
    for sid, slide_path in enumerate(input_paths):
        seg_channel = channels[sid]
        threshold = thresholds[sid]

        # segment
        regions = _segment(slide_path, seg_channel, threshold)
        custom_callback.emit((sid, len(regions)))

        # crop
        with SlideImage(slide_path) as slide:
            for rid, region in enumerate(regions):

                _make_ome(slide, output_dirs[sid], region, rid)
                progress_callback.emit((sid, rid))
                count += 1
