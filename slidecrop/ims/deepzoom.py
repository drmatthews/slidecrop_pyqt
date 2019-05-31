import os
import sys
import math
from io import BytesIO
from multiprocessing import Process, JoinableQueue
from optparse import OptionParser

from PIL import Image
from xml.etree.ElementTree import ElementTree, Element, SubElement

from .slide import SlideImage


class DeepZoomGenerator:
    """Generates Deep Zoom tiles and metadata."""

    def __init__(self, slide, tile_size=256, overlap=1):
        """
        Create a DeepZoomGenerator wrapping an SlideImage object.

        :param slide:       a slide object.
        :param tile_size:   the width and height of a single tile.
        :param overlap:     the number of extra pixels to add to 
                            each interior edge of a tile.
        """

        # We have four coordinate planes:
        # - Row and column of the tile within the Deep Zoom level (t_)
        # - Pixel coordinates within the Deep Zoom level (z_)
        # - Pixel coordinates within the slide level (l_)
        # - Pixel coordinates within slide level 0 (l0_)

        self._slide = slide
        self._z_t_downsample = tile_size
        self._z_overlap = overlap
        # Precompute dimensions
        # Slide level
        self._l_dimensions = slide.slide_dimensions
        self._l0_offset = (0, 0)
        # print('self._l_dimensions = {}'.format(self._l_dimensions))
        self._l0_dimensions = self._l_dimensions[0]
        # #print('self._l0_dimensions=',self._l0_dimensions)
        # # Deep Zoom level
        z_size = self._l0_dimensions
        # #print('z_size=',z_size)
        z_dimensions = [z_size]
        while z_size[0] > 1 or z_size[1] > 1:
            z_size = tuple(max(1, int(math.ceil(z / 2))) for z in z_size)
            z_dimensions.append(z_size)
        self._z_dimensions = tuple(reversed(z_dimensions))
        # print('self._z_dimensions = {}'.format(self._z_dimensions))
        # # Tile
        # tiles = lambda z_lim: int(math.ceil(z_lim / self._z_t_downsample))
        # self._t_dimensions = tuple((tiles(z_w), tiles(z_h))
        #             for z_w, z_h in self._z_dimensions)
        # #print('self._t_dimensions=',self._t_dimensions)
        # Deep Zoom level count
        #print ('_z_dimensions=',self._z_dimensions)
        self._dz_levels = len(self._z_dimensions)

        # Total downsamples for each Deep Zoom level
        l0_z_downsamples = tuple(2 ** (self._dz_levels - dz_level - 1)
                    for dz_level in range(self._dz_levels))
        # print('l0_z_downsamples = {}'.format(l0_z_downsamples))

        # Preferred slide levels for each Deep Zoom level
        self._slide_from_dz_level = tuple(
                    self._slide.get_best_level_for_downsample(d)
                    for d in l0_z_downsamples)

        tiles = lambda z_lim: int(math.ceil(z_lim / self._z_t_downsample))
        # print(tiles)
        self._t_dimensions = tuple((tiles(z_w), tiles(z_h))
                    for z_w, z_h in self._z_dimensions)
        # print(self._t_dimensions)

        # Piecewise downsamples
        self._l0_l_downsamples = self._slide.level_downsamples
        self._l_z_downsamples = tuple(
                    l0_z_downsamples[dz_level] / self._l0_l_downsamples[self._slide_from_dz_level[dz_level]]
                    for dz_level in range(self._dz_levels))

    @property
    def level_count(self):
        """The number of Deep Zoom levels in the image."""
        return self._dz_levels

    @property
    def level_tiles(self):
        """A list of (tiles_x, tiles_y) tuples for each Deep Zoom level."""
        return self._t_dimensions

    @property
    def tile_count(self):
        """The total number of Deep Zoom tiles in the image."""
        return sum(t_cols * t_rows for t_cols, t_rows in self._t_dimensions)        

    def _l0_from_l(self, slide_level, l):
        return self._l0_l_downsamples[slide_level] * l

    def _l_from_z(self, dz_level, z):
        return self._l_z_downsamples[dz_level] * z

    def _z_from_t(self, t):
        return self._z_t_downsample * t

    def _get_tile_info(self, dz_level, t_location):
        # Check parameters
        if dz_level < 0 or dz_level >= self._dz_levels:
            raise ValueError("Invalid level")
        for t, t_lim in zip(t_location, self._t_dimensions[dz_level]):
            if t < 0 or t >= t_lim:
                raise ValueError("Invalid address")

        # Get preferred slide level
        slide_level = self._slide_from_dz_level[dz_level]

        # Calculate top/left and bottom/right overlap
        z_overlap_tl = tuple(self._z_overlap * int(t != 0)
                    for t in t_location)
        z_overlap_br = tuple(self._z_overlap * int(t != t_lim - 1)
                    for t, t_lim in
                    zip(t_location, self.level_tiles[dz_level]))

        # Get final size of the tile
        z_size = tuple(min(self._z_t_downsample,
                    z_lim - self._z_t_downsample * t) + z_tl + z_br
                    for t, z_lim, z_tl, z_br in
                    zip(t_location, self._z_dimensions[dz_level],
                    z_overlap_tl, z_overlap_br))

        # Obtain the region coordinates
        z_location = [self._z_from_t(t) for t in t_location]
        l_location = [self._l_from_z(dz_level, z - z_tl)
                    for z, z_tl in zip(z_location, z_overlap_tl)]
        # Round location down and size up, and add offset of active area
        l_size = tuple(int(min(math.ceil(self._l_from_z(dz_level, dz)),
                    l_lim - math.ceil(l)))
                    for l, dz, l_lim in
                    zip(l_location, z_size, self._l_dimensions[slide_level]))

        # Return read_region() parameters plus tile size for final scaling
        return ((l_location, slide_level, l_size), z_size)

    def get_tile(self, level, address):
        """Return a numpy array for the tile.

        :param level:     the Deep Zoom level.
        :param address:   the address of the tile within the
                          level as a (col, row) tuple.
        """

        # Read tile
        args, z_size = self._get_tile_info(level, address)
        data = self._slide.read_region(*args)

        bg = Image.new('RGB', data.size, '#ffffff')
        tile = Image.composite(data, bg, tile)

        # Scale to the correct size
        if tile.size != z_size:
            tile.thumbnail(z_size, Image.ANTIALIAS)        

        return img

    def get_dzi(self, format):
        """Return a string containing the XML metadata for the .dzi file.

        :param format:    the format of the individual tiles ('png' or 'jpeg')
        
        """
        image = Element('Image', TileSize=str(self._z_t_downsample),
                        Overlap=str(self._z_overlap), Format=format,
                        xmlns='http://schemas.microsoft.com/deepzoom/2008')
        w, h = self._l0_dimensions
        SubElement(image, 'Size', Width=str(w), Height=str(h))
        tree = ElementTree(element=image)
        buf = BytesIO()
        tree.write(buf, encoding='UTF-8')
        return buf.getvalue().decode('UTF-8')