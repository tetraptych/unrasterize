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
        n = classes.Unrasterizer(mask_width=25)
        n.select_representative_pixels(self.raster_data)
        assert len(n.selected_pixels) == 33     # A posteriori.

    def test_windowed_unrasterizer(self):
        """Test that the WindowedUnrasterizer class selects pixels correctly."""
        n = classes.WindowedUnrasterizer(mask_width=25)
        n.select_representative_pixels(self.raster_data)
        assert len(n.selected_pixels) == 37     # A posteriori.

    def test_to_geojson_raises_error_if_no_points_are_selected(self):
        """An unrasterizer cannot be converted to GeoJSON if no points have been selected."""
        n = classes.BaseUnrasterizer()
        with pytest.raises(RuntimeError):
            n.to_geojson()

    def test_to_geojson(self):
        """Test that an unrasterizer can be converted to GeoJSON successfully."""
        n = classes.WindowedUnrasterizer(mask_width=25)
        n.select_representative_pixels(self.raster_data)
        jsonified = n.to_geojson(crs={'init': 'espg:4326'})
        assert len(jsonified['features']) == len(n.selected_pixels)

    def test_to_geopandas(self):
        """Test that an unrasterizer can be converted to a GeoDataFrame successfully."""
        n = classes.WindowedUnrasterizer(mask_width=25)
        n.select_representative_pixels(self.raster_data)
        gdf = n.to_geopandas(crs={'init': 'espg:4326'})
        assert gdf.shape[0] == len(n.selected_pixels)
        assert gdf.crs == {'init': 'espg:4326'}
