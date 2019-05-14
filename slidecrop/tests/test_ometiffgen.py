import time

from joblib import Parallel, delayed

from slidecrop.utils.ome_tiff_generator import OMETiffGenerator
from slidecrop.utils.slide import SlideImage
from slidecrop.utils.ome_tiff_generator import OMETiffGenerator
    
with SlideImage('.\\slidecrop\\test_data\\rgb.ims') as slide:

    outputdir = '.\\slidecrop\\test_data\\'
    channels = [0, 1, 2]
    regions = [
        [97, 11200, 1633, 1696],
        [1569, 19456, 1569, 1696],
        [4002, 27424, 1569, 1760]
    ]

    tic = time.time()
    for rid, region in enumerate(regions):
        filename = slide.basename + '_section_{}.ome.tif'.format(rid)
        ometiff = OMETiffGenerator(
            slide,
            filename,
            outputdir,
            channels, 0, 0
        )
        ometiff.run(region)
    toc = time.time()
    print(toc - tic)