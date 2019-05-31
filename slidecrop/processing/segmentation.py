from math import ceil

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from scipy.ndimage import binary_fill_holes, binary_erosion
from skimage.segmentation import clear_border
from skimage.measure import label, regionprops
from skimage.morphology import (
    closing, binary_closing, binary_opening, square
)
from skimage.color import label2rgb
from skimage.filters import (
    threshold_isodata,
    threshold_mean,
    threshold_otsu,
    threshold_triangle,
    threshold_yen
)


class RectRegion:

    def __init__(self, x0, y0, w, h, scale_factor):
        self.roi = [x0, y0, w, h]
        self.scale_factor = scale_factor
        self.segmentation_roi = self._scale(scale_factor)

    def _scale(self, scale_factor):
        return [
            ceil(self.roi[0] * scale_factor[0]),
            ceil(self.roi[1] * scale_factor[1]),
            ceil(self.roi[2] * scale_factor[0]),
            ceil(self.roi[3] * scale_factor[1])
        ]

    def __getitem__(self, key):
        return self.segmentation_roi[key]
        

class Segment:

    def __init__(self, mode, scale_factor, channel=None,
                 thresh_method='auto', threshold=None):

        self.mode = mode
        self.scale_factor = scale_factor
        self.threshold_method = thresh_method
        self.threshold = threshold
        if channel:
            self.channel = channel
        else:
            # auto find best segmentation channel
            # set to 0 for now
            self.channel = 0

    def _apply_threshold(self, plane, thresh):
        if 'bright' in self.mode:
            return plane < thresh
        elif 'fluoro' in self.mode:
            return plane > thresh

    def _auto_threshold(self, plane, method='otsu'):
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
            raise NotImplementedError(
                'thresholding method not supported'
            )
        return self._apply_threshold(plane, thresh)

    def _manual_threshold(self, plane, thresh):
        return self._apply_threshold(plane, thresh)

    def _close_binary(self, binary, kernel=3):
        return binary_closing(binary, square(kernel))

    def _open_binary(self, binary, kernel=3):
        return binary_opening(binary, square(kernel))

    def _fill_holes(self, binary, kernel=3):
        fillsize = (kernel, kernel)
        bw = binary_fill_holes(
            binary, structure=np.ones(fillsize)
        )
        return bw

    def _erode(self, binary, kernel=3, eroiter=1):
        erosize = (kernel, kernel)
        bw = binary_erosion(
            binary, structure=np.ones(erosize), iterations=eroiter
        )
        return bw

    def _clear(self, binary):
        return clear_border(binary)

    def _find_regions(self, binary, image, scale_factor):
        label_image = label(binary)
        # image_label_overlay = label2rgb(label_image, image=image)

        # fig, ax = plt.subplots(figsize=(10, 6))
        # ax.imshow(image_label_overlay)
        regions = []
        for region in regionprops(label_image):
            # take regions with large enough areas
            if region.area >= 100:
                # draw rectangle around segmented coins
                minr, minc, maxr, maxc = region.bbox
                regions.append([minc, minr, maxc - minc, maxr - minr])
                # rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
                #                         fill=False, edgecolor='red', linewidth=2)
                # ax.add_patch(rect)

        # ax.set_axis_off()
        # plt.tight_layout()
        # plt.show()
        regions = sorted(regions)
        scaled_regions = []
        for region in regions:
            scaled_regions.append(
                RectRegion(*region, scale_factor)
            )

        return scaled_regions

    def run(self, image):

        plane = image[self.channel, :, :]
        if 'manual' in self.threshold_method:
            bw = self._manual_threshold(plane, self.threshold)
        else:
            bw = self._auto_threshold(plane)

        bw = self._close_binary(bw)
        # bw = open_binary(bw)
        # bw = fill_holes(bw)
        # bw = erode(bw)
        bw = self._clear(bw)
        return self._find_regions(bw, plane, self.scale_factor)