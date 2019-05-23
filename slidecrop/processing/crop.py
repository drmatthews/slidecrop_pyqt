import os
import time

from ..ims.slide import SlideImage
from ..ome.ometiff import OMETiffGenerator
from .segmentation import Segment


class CropSlide:

    def __init__(self, slide, outputdir, crop_channels=None,
                 crop_level=None, seg_channel=0, seg_level=None,
                 threshold_method='manual', threshold=None,
                 rotation=0, skip_segmentation=False):

        # self.slide = SlideImage(slidepath)
        self.slide = slide
        if not slide.is_closed:
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
            self.threshold = threshold
            if 'manual' in self.threshold_method:
                if self.threshold is None:
                    raise ValueError('You must supply a value for thresholding')

            self.rotation = rotation
            self.skip_segmentation = skip_segmentation
            self._crop()
            self.slide.close()
        else:
            raise ValueError('The slide has been closed - repoen to crop')

    def _segment(self):
        image = self.slide.low_resolution_image()
        try:
            segmenter = Segment(
                self.mode, self.scale_factor, channel=self.seg_channel,
                thresh_method=self.threshold_method, threshold=self.threshold
            )
            return segmenter.run(image)
        except:
            raise IOError('Could not segment slide')

    def _crop(self):

        if not self.skip_segmentation:
            regions = self._segment()
        else:
            regions = self.slide.regions

        try:
            for rid, region in enumerate(regions):
                print(rid)
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
        except:
            raise IOError('Could not crop slide')