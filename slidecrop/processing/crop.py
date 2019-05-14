import os
import time

from slidecrop.ims.slide import SlideImage
from slidecrop.processing.segmentation import SegmentSlide
from slidecrop.ome.ome_tiff_generator import OMETiffGenerator


class CropSlide:

    def __init__(self, slidepath, outputdir, crop_channels=None,
                 crop_level=None, seg_channel=0, seg_level=None,
                 threshold_method='manual', threshold=None,
                 rotation=0):

        self.slide = SlideImage(slidepath)
        self.original_metadata = self.slide.metadata        
        self.mode = self.slide.microscope_mode
        self.scale_factor = self.slide.scale_factor

        self.outputdir = outputdir
        self.crop_channels = crop_channels
        if crop_channels is None:
            self.crop_channels = [c for c in range(self.slide.size_c)]

        self.crop_level = crop_level
        if crop_level is None:
            self.crop_level = self.slide.crop_level

        self.seg_channel = seg_channel
        self.seg_level = seg_level
        if seg_level is None:
            self.seg_level = self.slide.segmentation_level

        self.threshold_method = threshold_method
        if 'manual' in self.threshold_method:
            try:
                self.threshold = threshold
            except:
                print('You must supply a value for thresholding')
        self.rotation = rotation
        self._crop()


    def _segment(self):
        plane = self.slide.low_resolution_image()
        segmenter = SegmentSlide(
            self.mode, self.scale_factor, channel=self.seg_channel,
            thresh_method='manual', threshold=self.threshold
        )
        return segmenter.run(plane)

    def _crop(self):
        regions = self._segment()
        tic = time.time()
        for rid, region in enumerate(regions):
            print(region.roi)
            filename = (
                self.slide.basename + '_section_{}.ome.tif'.format(rid)
            )
            ometiff = OMETiffGenerator(
                self.slide,
                filename,
                self.outputdir,
                self.crop_channels,
                self.crop_level,
                self.rotation
            )
            ometiff.run(region)

        toc = time.time()
        print(toc - tic)

        self.slide.close()