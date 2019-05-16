import os
from math import floor
from tempfile import mkdtemp
import os.path as path
import datetime
from uuid import uuid4 as uuid

import numpy as np
from tifffile import memmap, imwrite
from matplotlib import pyplot as plt

from .omexml import OMEXML

comment = """<!-- Warning: this comment is an OME-XML metadata block, which contains"
                  crucial dimensional parameters and other important metadata. Please edit
                  cautiously (if at all), and back up the original data before doing so.
                  For more information, see the OME-TIFF documentation:
                  https://docs.openmicroscopy.org/latest/ome-model/ome-tiff/ -->"""

def xsd_now():
    '''Return the current time in xsd:dateTime format'''
    return datetime.datetime.now().isoformat()

DEFAULT_NOW = xsd_now()

NS_DEFAULT = "http://www.openmicroscopy.org/Schemas/{ns_key}/2016-06"

default_xml = """<?xml version="1.0" encoding="UTF-8"?>
<OME xmlns="http://www.openmicroscopy.org/Schemas/OME/2016-06"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:schemaLocation="http://www.openmicroscopy.org/Schemas/OME/2016-06 http://www.openmicroscopy.org/Schemas/OME/2016-06/ome.xsd">
    <Instrument ID="Instrument:0">
        <Objective ID="Objective:0" NominalMagnification="9.96"></Objective>
    </Instrument>
    <Image ID="Image:0" Name="default.png">
        <AcquisitionDate>%(DEFAULT_NOW)s</AcquisitionDate>
        <Pixels BigEndian="false"
                DimensionOrder="XYCZT"
                ID="Pixels:0"
                Interleaved="false"
                SizeC="1"
                SizeT="1"
                SizeX="512"
                SizeY="512"
                SizeZ="1"
                Type="uint8">
            <Channel ID="Channel:0:0" Color="65535" SamplesPerPixel="1">
                <LightPath/>
            </Channel>
        </Pixels>
    </Image>
</OME>""".format(ns_ome_default=NS_DEFAULT.format(ns_key='ome'))


class OMETiffGenerator:
    """
    Creates a single TIFF image from a region
    cropped from an slide scanner image (*.ims format)
    """    
    def __init__(self, slide, filename, outputdir, 
                 channels, level, rotation):
        """
        Constructor

        :param slide: SlideImage instance
        :type slide: SlideImage class instance
        :param filename: filename of *.ome.tiff being written
        :type filename: str
        :param outputdir: directory where *.ome.tiff will be saved
        :type outputdir: str
        :param channels: the channels to be written
        :type channels: list or int
        :param level: the resolution level that has been cropped
        used when getting pixels from the slide
        :type level: int
        :param rotation: the rotation to applied when writing
        :type rotation: int
        """
        self.slide = slide
        self.filename = filename
        print(self.filename)
        self.crop_level = level
        self.rotation = rotation
        self.outputpath = os.path.join(outputdir, self.filename)
        print(outputdir)
        self.tile_width = 1024
        self.tile_height = 1024
        self.channels = channels

    def get_num_channels(self):
        """
        :returns number of channels being written
        """
        print(self.channels)
        return (
            len(self.channels) if isinstance(self.channels, list) else 0
        )

    # this feels like it's in the wrong place
    # and crop level should be accessed elsewhere
    # TODO: refactor
    def _get_slide_data(self, channel, x, y, w, h):
        """
        :returns pixels being written as numpy array
        """
        roi = [x + self.roi[0], y + self.roi[1], w, h]
        return self.slide.get_pixels(
            self.crop_level, channel, region=roi
        )

    def _process_channel_color(self, color):
        """
        Convert RGB color to 32 bit int

        :returns channel color as 32 bit int
        """
        rgb = [int(float(c)*255) for c in color.split(" ")]
        rgba = (rgb[0]<<24) + (rgb[1]<<16) + (rgb[2]<<8) + 255
        if rgba >= (2**32 / 2) - 1:
            rgba = (2**32 - rgba) *(-1)
        return rgba

    def _mk_uuid(self):
        """
        UUID for PixelData
        :returns uuid
        """
        return 'urn:uuid:{}'.format(uuid())

    def make_xml(self, metadata):
        """
        Constructs the ome-xml metadata
        :param metadata: original slide metadata
        :type metdata: dict
        :returns ome-xml metadata as str
        """
        xml = OMEXML(default_xml)

        # set Instrument
        instr_id = metadata['MicroscopeMode']
        xml.Instrument.ID = instr_id

        # set Objective
        xml.Objective.NominalMagnification = metadata['LensPower']

        # set Image AcquisitionDate
        date = metadata['RecordingDate']
        xml.image().AcquisitionDate = date.replace(' ','T')

        # set Image Name
        xml.image().Name = self.filename

        # set Description
        # slidename = metadata['FileName']
        # xml.image().Description = (
        #     "Region {0} out of {1} from {1}".
        #     format(section_id, num_sections, slidename)
        # )

        # set Image sizes
        xml.image().Pixels.SizeC = str(self.size_c)
        xml.image().Pixels.SizeX = str(self.size_x)
        xml.image().Pixels.SizeY = str(self.size_y)
        xml.image().Pixels.SizeZ = '1'
        xml.image().Pixels.PhysicalSizeX = metadata['crop_xresolution']
        xml.image().Pixels.PhysicalSizeY = metadata['crop_yresolution']
        xml.image().Pixels.PhysicalSizeZ = metadata['crop_zresolution']

        # set channels
        xml.image().Pixels.channel_count = self.size_c
        for c in range(self.size_c):
            channel = metadata['Channel {}'.format(c)]
            xml.image().Pixels.Channel(c).Name = channel['Name']
            xml.image().Pixels.Channel(c).ID = 'Channel:0:{}'.format(c)
            color = self._process_channel_color(channel['Color'])
            xml.image().Pixels.Channel(c).Color = color

        # set tiffdata
        slices = self.size_c * self.size_z * self.size_t
        uuid = self._mk_uuid()
        xml.image().Pixels.tiffdata_count = slices
        for s in range(slices):
            xml.image().Pixels.TiffData(s).IFD = s
            xml.image().Pixels.TiffData(s).FirstC = s
            xml.image().Pixels.TiffData(s).FirstZ = 0
            xml.image().Pixels.TiffData(s).FirstT = 0
            xml.image().Pixels.TiffData(s).PlaneCount = 1
            xml.image().Pixels.TiffData(s).UUID.FileName = self.filename
            xml.image().Pixels.TiffData(s).UUID.UUID_text = uuid

        return xml.to_xml()

    def write_tiles(self):
        """
        If the region cropped has a size in pixels
        above 4096 in any dimension the *.ome.tiff will
        be written as tiled data using a numpy memmap.
        Writing of the *.ome.tiff is done using tifffile.

        :returns number of tiles written
        """
        tw = self.tile_width
        th = self.tile_height
        size_x = self.size_x
        size_y = self.size_y
        size_c = self.size_c

        # initialise the numpy memmap
        fp = memmap(
            self.outputpath,
            dtype='uint8',
            mode='r+',
            shape=(size_c, size_y, size_x),
            description=self.xml,
            photometric='MINISBLACK'
        )

        tile_count = 0
        for c in range(0, self.size_c):
            channel = self.channels[c]

            for tile_offset_y in range(0, floor((size_y + th - 1) / th)):

                for tile_offset_x in range(0, floor((size_x + tw - 1) / tw)):

                    x = tile_offset_x * tw
                    y = tile_offset_y * tw
                    
                    w = tw
                    if (w + x > size_x):
                        w = size_x - x

                    h = th
                    if (h + y > size_y):
                        h = size_y - y
                    
                    # get the pixel data out of the SlideImage
                    chunk = self._get_slide_data(channel, x, y, w, h)
                    print(chunk.shape)
                    if (w != chunk.shape[-1]) or (h != chunk.shape[-2]):
                        w = chunk.shape[-1]
                        h = chunk.shape[-2]

                    # add the data to the memmap
                    # TODO: apply rotation
                    fp[c, y: y + h, x: x + w] = chunk[:, :]
                    fp.flush()
        del fp
        return tile_count

    def write_plane(self):
        """
        If the region cropped has a size in pixels
        less than or equal to 4096 for both dimensions
        the pixel data will be in memory and will be
        written to *.ome.tiff in one go.
        """
        size_x = self.size_x
        size_y = self.size_y
        size_c = self.size_c

        image_data = np.zeros((size_c, size_y, size_x), dtype=np.uint8)
        print('num channels = {}'.format(size_c))
        for c in range(size_c):

            channel = self.channels[c]
            imarray = self._get_slide_data(channel, 0, 0, self.roi[-2], self.roi[-1])
            print('imarray shape: {}'.format(imarray.shape))
            
            print('Writing channel:  {}'.format(c + 1))
            if self.rotation == 0:
                plane = imarray[:] 
            if self.rotation == 1:
                plane = np.rot90(imarray[:], 1)
            elif self.rotation == 2:
                plane = np.rot90(imarray[:], 3)
                
            image_data[c, :, :] = plane

        imwrite(
            self.outputpath,
            image_data,
            shape=(size_c, size_y, size_x),
            description=self.xml,
            photometric='MINISBLACK'
        )

    def run(self, region):
        """
        Access point to the class. Determines whether to
        write tiled data or not.

        :param region: x, y, w, h of region to be written to *.ome.tiff
        :type region: list
        """
        self.size_x = region[-2]
        self.size_y = region[-1]
        self.size_c = self.get_num_channels()
        print(self.size_c)
        self.size_t = 1
        self.size_z = 1
        self.roi = region
        self.xml = self.make_xml(self.slide.metadata)

        if self.size_x >= 4096 or self.size_y >= 4096:
            self.write_tiles()
        else:
            self.write_plane()