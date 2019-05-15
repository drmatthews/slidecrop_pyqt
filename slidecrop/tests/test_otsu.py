import numpy as np

from slidecrop.ims.slide import SlideImage
from slidecrop.utils.otsu import threshold_otsu

edges = np.arange(256)
with SlideImage('.\\slidecrop\\test_data\\rgb1.ims') as slide:

    for c in range(slide.size_c):

        hist = slide.get_histogram(c=c)
        # print(hist.shape)
        # print(threshold_otsu(hist, edges))
        lo = slide.low_resolution_image()
        plane = lo[c, :, :]
        thresh = threshold_otsu(hist, show_plot=True)
        print(thresh)
