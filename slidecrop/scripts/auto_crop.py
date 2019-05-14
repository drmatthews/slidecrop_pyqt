import os
import argparse

from slidecrop.utils.slide import SlideImage
from slidecrop.utils.ome_tiff_generator import OmeTiffGenerator


def crop_slide(filepath, parameters):

    with SlideImage(filepath) as slide:
        regions = OmeTiffGenerator(slide, *parameters)


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--filename', help='name of file to be cropped', default='rgb.ims')
    parser.add_argument('--inputdir', help='directory in which the slide file resides', default='../test_data/')
    parser.add_argument('--outputdir', help='optionally specify an output directory')
    parser.add_argument('--crop_level', help='resolution level to be cropped - default is best resolution')

    args = parser.parse_args()
    parameters = {}
    outputdir = args.inputdir
    if args.outputdir:
        outputdir = args.outputdir
    filepath = os.path.join(args.filename, args.filepath)

    crop_level = 0
    if args.crop_level:
        crop_level = args.crop_level

    threshold = 'otsu'
    rotation = 0
    parameters = [outputdir, crop_level, threshold, rotation]           
    crop_slide(filepath, parameters)    