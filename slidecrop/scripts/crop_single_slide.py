import os
import argparse

from ..ims.slide import SlideImage
from ..processing.crop import CropSlide


def crop_slide(*args, **kwargs):
    CropSlide(*args, **kwargs)


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--filepath', help='full path to slide to be cropped')
    parser.add_argument('--outputdir', help='optionally specify an output directory')
    parser.add_argument('--crop_level', help='resolution level to be cropped - default is best resolution')
    parser.add_argument('--seg_level', help='resolution level to be segmented - default is lowest resolution')    
    parser.add_argument(
        '--threshold_method',
        help=('method used for automatic thresholding -'
              'Isodata, Mean, Otsu, Triangle or Yen')
    )
    parser.add_argument(
        '--threshold',
        help=('threshold value to use for manual thresholding')
    )    
    parser.add_argument(
        '--segmentation_channel',
        help=('channel to used for segmentation'),
    )    

    args = parser.parse_args()
    parameters = {}
    filepath = args.filepath
    inputdir = os.path.dirname(filepath)
    outputdir = inputdir
    if args.outputdir:
        outputdir = args.outputdir

    crop_level = None
    if args.crop_level:
        crop_level = args.crop_level

    threshold_method = 'otsu'
    if args.threshold_method:
        threshold_method = args.threshold_method

    threshold = None
    if args.threshold:
        threshold = float(args.threshold)

    seg_channel = 0
    if args.segmentation_channel:
        seg_channel = int(args.segmentation_channel)

    seg_level = None
    if args.segmentation_channel:
        seg_channel = int(args.segmentation_channel)

    rotation = 0
    parameters = [
        filepath, outputdir, crop_level,
        seg_channel, threshold_method, rotation
    ]
    crop_slide(filepath, outputdir, crop_level=crop_level,
               seg_channel=seg_channel, seg_level=seg_level,
               threshold_method=threshold_method,
               threshold=threshold, rotation=rotation)