from ..ims.slide import SlideImage
from ..processing.segmentation import SegmentSlide
    
with SlideImage('.\\test_data\\rgb1.ims') as slide:
    mode = slide.microscope_mode
    dims = slide.slide_dimensions
    lo = slide.low_resolution_image()
    factor = slide.scale_factor

segmenter = SegmentSlide(mode, factor)
regions = segmenter.run(lo)

for region in regions:
    print(region.segmentation_roi)