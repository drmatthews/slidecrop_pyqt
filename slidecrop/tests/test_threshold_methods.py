import matplotlib.pyplot as plt

from skimage import data
from skimage.filters import try_all_threshold

from ..ims.slide import SlideImage


with SlideImage('.\\test_data\\rgb1.ims') as slide:

    low = slide.low_resolution_image()
    plane = low[2, :, :]

    fig, ax = try_all_threshold(plane, figsize=(10, 8), verbose=False)
    plt.show()