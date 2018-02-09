"""Tests for all unrasterizer classes."""
import pytest

import rasterio

from unrasterize import classes


class TestUnrasterizers():
    """Test that unrasterizers work as expected."""

    def setup(self):
        """Initialize test class with raster file."""
        self.raster_path = 'data/Belize/BLZ_ppp_v2b_2015_UNadj.tif'
        self.raster_data = rasterio.open(self.raster_path)

    def test_base_unrasterizer_raises_not_implemented_error(self):
        """The BaseRasterizer should not implement the select_representative_pixels method."""
        n = classes.BaseUnrasterizer()
        with pytest.raises(NotImplementedError):
            n.select_representative_pixels(self.raster_data)

    def test_naive_unrasterizer(self):
        """Test that the NaiveUnrasterizer class selects the expected number of pixels."""
        n_pixels = 25
        n = classes.NaiveUnrasterizer(n_pixels=n_pixels)
        n.select_representative_pixels(self.raster_data)
        assert len(n.selected_pixels) == n_pixels
        assert len(n.selected_values) == n_pixels
        assert len(n.selected_coords) == n_pixels

    def test_vanilla_unrasterizer(self):
        """Test that the Unrasterizer class selects pixels correctly."""
        mask_width = 25
        n = classes.Unrasterizer(mask_width=mask_width)
        n.select_representative_pixels(self.raster_data)
        print(len(n.selected_pixels))

    def test_windowed_unrasterizer(self):
        """Test that the WindowedUnrasterizer class selects pixels correctly."""
        mask_width = 25
        n = classes.WindowedUnrasterizer(mask_width=mask_width)
        n.select_representative_pixels(self.raster_data)
        print(len(n.selected_pixels))
