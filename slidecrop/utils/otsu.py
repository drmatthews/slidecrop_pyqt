import numpy as np


def threshold_otsu(slide_hist, nbins=256, bin_width=1.0, show_plot=False):
    """
    Use Otsu's method to find threshold. Borrowed from scikit-image

    :param slide_hist: historgram retrieved from slide metadata
    :type slide_hist: numpy array
    """

    # remove non zeros and the last three bins - for
    # bright field images there is usually a huge number
    # of pixels with close to the maximum grey level value
    # on the camera
    hist = slide_hist[np.nonzero(slide_hist)]
    hist = hist[:-3]
    bin_centers = np.arange(nbins) + bin_width / .5
    bin_centers = bin_centers[np.nonzero(slide_hist)]
    bin_centers = bin_centers[:-3]

    # class probabilities for all possible thresholds
    weight1 = np.cumsum(hist)
    # print(weight1)
    weight2 = np.cumsum(hist[::-1])[::-1]
    # class means for all possible thresholds
    mean1 = np.cumsum(hist * bin_centers) / weight1
    mean2 = (np.cumsum((hist * bin_centers)[::-1]) / weight2[::-1])[::-1]

    # Clip ends to align class 1 and class 2 variables:
    # The last value of `weight1`/`mean1` should pair with zero values in
    # `weight2`/`mean2`, which do not exist.
    variance12 = weight1[:-1] * weight2[1:] * (mean1[:-1] - mean2[1:]) ** 2

    idx = np.argmax(variance12)
    threshold = bin_centers[:-1][idx]

    # for testing only
    if show_plot:
        import matplotlib.pyplot as plt        
        plt.figure()
        plt.plot(bin_centers, hist)
        plt.semilogy()
        plt.vlines(threshold, 0, np.max(hist))
        plt.show()

    return threshold
