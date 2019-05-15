import numpy as np

from slidecrop.ims.slide import SlideImage
from slidecrop.utils.otsu import threshold_otsu

edges = np.arange(256)
with SlideImage('.\\slidecrop\\test_data\\rgb1.ims') as slide:

    thresholds = []
    for c in range(slide.size_c):

        hist = slide.get_histogram(c=c)
        # print(hist.shape)
        # print(threshold_otsu(hist, edges))
        lo = slide.low_resolution_image()
        plane = lo[c, :, :]
        thresh = threshold_otsu(hist, show_plot=False)
        thresholds.append(thresh)

    plane = lo[0, :, :]
    bw = plane < thresholds[0]
    print(thresh)

    import matplotlib.pyplot as plt

    plt.figure()
    plt.imshow(bw)
    plt.show()
