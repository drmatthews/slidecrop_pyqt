import os
import math

import h5py
import numpy as np


class SlideImage:
    """
    Interface to slide scanner image stored in 
    BitPlane Imaris *.ims format.

    The underlying file format is *.hdf and as such the 
    h5py module is used to read and access the file.

    Can be used as follows:
    1. slide = SlideImage(path)
       # process
       slide.close()
    2. with SlideImage(path) as slide:
           # process

    """
    def __init__(self, filepath):
        """
        Constructor
        :param filepath: path to the slide image in *.ims format
        :type filepath: str
        """
        if filepath.endswith('ims') and os.path.exists(filepath):
            self.filepath = filepath
            filename = os.path.basename(filepath)
            self.basename = os.path.splitext(filename)[0]
            self.slide = h5py.File(filepath,'r')
            self.num_levels = self.resolution_levels()
            self.size_c = self.channels()
            self.size_t = self.time_points()            
            self._segmentation_level = self.num_levels - 1
            self._crop_level = 0
            self._scale_factor = self.scale_factor
            self._microscope_mode = ''
            self.is_closed = False
        else:
            raise IOError('File does not exist or is not an ims file')

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.slide.close()

    def _bytes_to_int(self, byte_list):
        """
        Integer values are stored in HDF metadata as byte strings

        :param byte_list: list of byte strings
        :returns list of ints
        """
        return int(b''.join(byte_list).decode('utf-8'))

    def _bytes_to_str(self, byte_list):
        """
        String values are stored in HDF metadata as byte strings
        :param byte_list: list of byte strings
        :returns list of str
        """
        return str(b''.join(byte_list).decode('utf-8'))

    def open(self):
        """
        Create an h5py file handle
        """
        if self.filepath and self.is_closed:
            self.slide = h5py.File(self.filepath,'r')
            self.is_closed = False
            
    def close(self):
        """
        Close the HDF5 file handle
        """
        self.slide.close()
        self.is_closed = True

    def get_histogram(self, r=None, t=0, c=0):
        """
        Channel histograms are stored in *.ims file metadata

        :param r: resolution level
        :type r: int
        :param t: time point
        :type t: int
        :param c: channel
        :type c: int
        :returns histogram as numpy array
        """
        if r is None:
            r = self.segmentation_level

        if r <= self.num_levels - 1:
            histpath = (
                '/DataSet/ResolutionLevel {0}/TimePoint {1}/Channel {2}/'.
                format(r, t, c)
            )
            hist = self.slide[histpath]['Histogram'][:]
            return hist

    def resolution_levels(self):
        """
        Number of slide resolution levels

        :returns number of resolution levels
        """
        levels = len(self.slide['/DataSet'])
        return levels if levels is not None else 0

    def channels(self):
        """
        Number of slide channels

        :returns number of channels
        """        
        channels = len(self.slide['/DataSet/ResolutionLevel 0/TimePoint 0/'])
        return channels if channels is not None else 0

    def time_points(self):
        """
        Number of slide time points (usually 1)

        :returns number of time points
        """        
        time_points = len(self.slide['/DataSet/ResolutionLevel 0/'])
        return time_points if time_points is not None else 0

    def level_dimensions(self, r):
        """
        xy dimensions (pixels) for a resolution level
        :param r: resolution level
        :type r: int
        :returns tuple of xy size
        """
        if r <= self.num_levels - 1:
            path = '/DataSet/ResolutionLevel {}/TimePoint 0/'.format(r)
            folder = 'Channel 0'
            size_x_bytes = self.slide[path + folder].attrs.get('ImageSizeX')
            size_x = self._bytes_to_int(size_x_bytes)
            size_y_bytes = self.slide[path + folder].attrs.get('ImageSizeY')
            size_y = self._bytes_to_int(size_y_bytes)

            return (size_x, size_y)
        else:
            return None

    def get_pixels(self, r, c, t=0, region=None):
        """
        Get pixel data from the *.ims image
        Note that the data is stored in the HDF5 image
        as chunks. This plays no role in data access.

        :param r: resolution level
        :type r: int
        :param c: channel
        :type c: int
        :param t: time point
        :type t: int
        :param region: x, y, w, h of the region to access
        :type regions: list
        :returns pixels of selected region as numpy array
        """
        # region should be x0, y0, w, h
        impath = (
            '/DataSet/ResolutionLevel {0}/TimePoint {1}/Channel {2}'.
            format(r, t, c)
        )
        try:
            data = self.slide[impath]['Data']
            plane_size = self.slide_dimensions[r]
            if region is None:
                region = np.zeros((4), dtype=np.uint16)
                region[0] = 0
                region[1] = 0
                region[2] = plane_size[0]
                region[3] = plane_size[1]

            row_min = region[1]
            col_min = region[0]
            row_max = region[1] + region[3]
            col_max = region[0] + region[2]

            return data[0, row_min:row_max, col_min: col_max]
        except:
            return None

    def low_resolution_image(self, r=None):
        """
        Get the whole slide image from the level
        specified or whichever level is currently
        set as the segmentation level

        :param r: resolution level
        :type r: int
        :returns whole slide image as numpy array
        """        
        if r is None:
            r = self.segmentation_level

        if r <= self.num_levels - 1:
            low_res_size = self.level_dimensions(r)
            low_res = np.zeros((self.size_c, low_res_size[-1], low_res_size[-2]))
            for c in range(self.size_c):
                low_res[c, :, :] = self.get_pixels(r, c)

            return low_res
        else:
            raise IOError('Resolution level not found - maximum level is {}'.format(self.num_levels - 1))

    def get_level_downsample(self, level):
        size0 = self.level_dimensions(0)
        # print('size0 {}'.format(size0))
        levelSize = self.level_dimensions(level)
        # print('level size {}'.format(levelSize))
        down_sample = tuple(
            map(lambda x, y: math.floor(float(x) / float(y)),
            size0, levelSize)
        )
        return max(down_sample)

    def get_best_level_for_downsample(self, down_sample):
        #return the best level for the required down sample
        level_count = self.resolution_levels()
        if down_sample < self.get_level_downsample(0):
            return 0

        for i in range(level_count):
            if down_sample < self.get_level_downsample(i):
                print(i - 1)
                return i - 1

        if down_sample >= self.get_level_downsample(level_count - 1):
            return level_count - 1

    def level_downsamples(self):
        """A list of downsampling factors for each level of the image.

        level_downsample[n] contains the downsample factor of level n."""
        level_count = self.resolution_levels()
        return tuple(
            self.get_level_downsample(i)
            for i in range(level_count)
        )

    @property
    def channel_names(self):
        """
        :returns list of channel names
        """
        names = []
        for channel in range(self.size_c):
            c = 'Channel {}'.format(channel)
            channel_group = '/DataSetInfo/{}'.format(c)
            name = self.slide[channel_group].attrs.get('Name')
            names.append(self._bytes_to_str(name))
        return names

    @property
    def channel_colors(self):
        """
        :returns list of channel colors
        """
        colors = []
        for channel in range(self.size_c):
            c = 'Channel {}'.format(channel)
            channel_group = '/DataSetInfo/{}'.format(c)
            color = self.slide[channel_group].attrs.get('Color')
            color_str = self._bytes_to_str(color)
            colors.append([float(c) for c in color_str.split(' ')])
        return colors

    @property
    def slide_dimensions(self):
        """
        :returns numpy array of xy dimensions for
        each resolution level
        """
        size_array = None
        if self.num_levels > 0:
            size_array = []
            for r in range(self.num_levels):
                size_array.append(self.level_dimensions(r))
            
        return size_array

    @property
    def scale_factor(self):
        """
        Scale factor upscales a region of a low resolution
        image to highest resolution level or whichever level
        is currently set to be the crop level.

        :returns tuple of xy scale factors
        """
        slide_size = self.slide_dimensions
        hi_level = slide_size[self._crop_level]
        low_level = slide_size[self._segmentation_level]
        xscale = float(hi_level[0]) / float(low_level[0])
        yscale = float(hi_level[1]) / float(low_level[1])
        return (xscale, yscale)

    @property
    def segmentation_level(self):
        """
        Resolution level to be used for segmentation

        :returns resolution level (int)
        """
        return self._segmentation_level

    @segmentation_level.setter
    def segmentation_level(self, value):
        """
        Sets the resolution level to be used for segmentation
        """
        if value <= self.num_levels - 1:
            self._segmentation_level = value
            self._scale_factor = self.scale_factor
        else:
            raise ValueError('Resolution level does not exist')

    @property
    def crop_level(self):
        """
        :returns resolution level to used for cropping
        """
        return self._crop_level

    @crop_level.setter
    def crop_level(self, value):
        """
        Sets the resolution level to be used for cropping
        """
        if value <= self.num_levels - 1:
            self._crop_level = value
        else:
            raise ValueError('Resolution level does not exist')

    @property
    def microscope_mode(self):
        """
        :returns microscope modality 'bright' or 'fluoro'
        """
        mm = self.slide['DataSetInfo/Image'].attrs.get('MicroscopeMode')
        mm = self._bytes_to_str(mm)
        if 'MetaCyte TL' in mm:
            self._microscope_mode = 'bright'
        elif 'MetaCyte FL' in mm:
            self._microscope_mode = 'fluoro'
        return self._microscope_mode

    def _group_attributes(self, group):
        """
        Private method used to get group attributes from
        HDF file.

        :returns dict of attributes
        """
        attributes = {}
        for attr in self.slide[group].attrs.items():
            attributes[attr[0]] = self._bytes_to_str(attr[-1])
        return attributes

    @property
    def metadata(self):
        """
        Extracts all group attributes from HDF file.

        :returns dict of attributes
        """        
        # as key, value pairs
        metadata = {}
        # DataSetInfo/Channel
        for channel in range(self.size_c):
            c = 'Channel {}'.format(channel)
            channel_group = '/DataSetInfo/{}'.format(c)
            metadata[c] = self._group_attributes(channel_group)

            mf = 'MF Capt Channel {}'.format(channel + 1)
            mf_group = '/DataSetInfo/{}'.format(mf)
            metadata[mf] = self._group_attributes(mf_group)

        groups = [
            '/DataSetInfo/Image',
            '/DataSetInfo/Imaris',
            '/DataSetInfo/ImarisDataSet'
        ]

        for group in groups:
            metadata.update(self._group_attributes(group))

        metadata['crop_scale_factor'] = self.scale_factor
        slidex = float(metadata['ExtMax0']) - float(metadata['ExtMin0'])
        slidey = float(metadata['ExtMax1']) - float(metadata['ExtMin1'])
        slidez = float(metadata['ExtMax2']) - float(metadata['ExtMin2'])
        metadata['crop_xresolution'] = str(slidex / self.slide_dimensions[self.crop_level][0])
        metadata['crop_yresolution'] = str(slidey / self.slide_dimensions[self.crop_level][1])
        metadata['crop_zresolution'] = str(slidez)
        return metadata


