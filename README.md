DESCRIPTION
-----------

This repository holds a reimplentation of the original 
[SlideCrop](https://github.com/QBI-Microscopy/SlideCrop "SlideCrop") app using
PyQt instead of WxPython.

The app allows a user to segment regions of microscope images recorded
using a MetaSystems slide scanner (either brightfield or fluorescence) and stored
in BitPlane Imaris (*.ims) format - no other file formats are currently
supported. The full resolution image is too large to be processed in 
memory so iamges are cropped by segmenting a low resolution version of the image
and upscaling the segmented regions to the full resolution. The resultant
images are saved as [OME-TIFF](https://docs.openmicroscopy.org/ome-model/5.6.3/ome-tiff/). If the region exceeds 4096 pixels in any dimension
the image is written as tiles so that large arrays are not held in memory. These huge
images (10's of Gb) can therefore be handled with very modest computing power.

This was done because:

1. To use QThreads to handle multi-threading. This is from the GUI perspective,
it still isn't possible to multi-thread the actual cropping of a single Imaris image
due to the fact that HDF does not allow access to the file in multiple threads. It
may be possible to utilise multiprocessing to handle batch crop of files but isn't
implemented as yet because it is not possible to have nested processes in a QThread.

2. The [original version](https://github.com/QBI-Microscopy/SlideCrop) (and the reimagined version [BatchCrop](https://github.com/QBI-Microscopy/BatchCrop)) uses a correction
factor when upscaling the low resolution segmented regions to the resolution
level being cropped. The reason this happens is that the image data is saved
to the file in chunks. This means that the image size reported by looking at
the dimensions of the data in the HDF file can be larger than the actual
image dimensions. The correct dimensions are obtained by looking at the
metadata, specifically at the "ImageSizeX" and "ImageSizeY" attributes in any
channel group for each resolution level. This means no correction factors are
required. At present no padding is applied to region segmented which means that
tight borders are sometimes possible.

This app allows the user to either segment the image based on the automatically
determined threshold level (determined using any [thresholding method](https://scikit-image.org/docs/dev/auto_examples/applications/plot_thresholding.html#sphx-glr-auto-examples-applications-plot-thresholding-py)
supplied by [scikit-image](https://scikit-image.org/)).
Manually drawing areas on a low resolution version of the slide scanner
image has not yet been implemented but regions produced automatically are editable.

This version does not rely on libtiff (the old version used a hack in Pylibtiff to write tiled
images) and uses TiffFile instead. When regions are > 4096 in any dimension the ome-tiff is written
as a tiled image using numpy memmaps.

INSTALLATION
------------

Requires:

Python 3.6+  
pyqt5  
pyqtgraph  
h5py  
numpy  
scipy  
matplotlib  
scikit-image  
tifffile  

It is recommended to install into a virtual environment.

Download, unzip and install from folder using:
```
pip install .
```

Install from Github using:
```
pip install git+https://github.com/drmatthews/slidecrop_pyqt.git
```