import time

from ..ome.ometiff import OMETiffGenerator
from ..ims.slide import SlideImage

    
with SlideImage('.\\test_data\\rgb1.ims') as slide:

    outputdir = '.\\test_data\\'
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