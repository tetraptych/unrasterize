"""Classes implementing methods to convert raster files to GeoJSON."""
import itertools
import math

import geojson

import geopandas as gpd

import numpy as np

import pathos

import rasterio

import shapely


class BaseUnrasterizer(object):
    """A base interface from which other unrasterization classes inherit."""

    def __init__(self):
        """Initialize a BaseUnrasterizer object."""
        self._selected_indexes = []
        self.selected_pixels = []
        self.selected_values = []
        self.selected_coords = []

    def select_representative_pixels(self, raster_data):
        """Select representative pixels for the provided raster dataset."""
        raise NotImplementedError

    def to_geojson(self, value_attribute_name='value', **extra):
        """Convert the selected points and values to GeoJSON."""
        if self.selected_coords is None or len(self.selected_coords) == 0:
            raise RuntimeError

        return geojson.FeatureCollection(
            features=[
                geojson.Feature(
                    id=id,
                    geometry=shapely.geometry.Point(coord),
                    properties={
                        value_attribute_name: float(value)
                    }
                )
                for id, (coord, value) in enumerate(zip(self.selected_coords, self.selected_values))
            ],
            **extra
        )

    def to_geopandas(self, value_attribute_name='value', **extra):
        """Convert the selected points and values to a GeoDataFrame."""
        feature_collection = self.to_geojson(value_attribute_name, **extra)
        return gpd.GeoDataFrame.from_features(
            features=feature_collection['features'],
            crs=feature_collection.get('crs', None)
        )

    @staticmethod
    def _sort_pixels(band):
        """
        Sort a band, returning the row, column indexes in descending order by value.

        Returns an array of the shape (band.size, 2).
        """
        return np.stack(
            np.unravel_index(
                indices=np.argsort(np.ravel(band))[::-1],
                dims=band.shape
            ),
            axis=-1
        )

    @staticmethod
    def _reassign_pixel_values(band, pixels, raw_pixel_values=[]):
        """Reweight values of selected pixels so that the total is preserved."""
        if not raw_pixel_values:
            raw_pixel_values = [band[tuple(pixel)] for pixel in pixels]
        # Avoid underflow by ignoring negative values.
        total = np.sum(band[band > 0.0], dtype=np.float32)
        total_selected = np.sum(raw_pixel_values, dtype=np.float32)
        return [
            val * total / total_selected for val in raw_pixel_values
        ]

    @staticmethod
    def _get_coordinates(transform, pixels, row_offset=0, col_offset=0):
        return [
            rasterio.transform.xy(
                transform=transform,
                rows=row + row_offset,
                cols=col + col_offset,
            )
            for row, col in pixels
        ]


class NaiveUnrasterizer(BaseUnrasterizer):
    """
    A naive implementation of the BaseUnrasterizer interface.

    Always chooses the pixels with the highest values. These pixels may be close together.
    """

    def __init__(self, n_pixels):
        """Initialize a NaiveUnrasterizer object."""
        super().__init__()
        self.n_pixels = n_pixels

    def select_representative_pixels(self, raster_data):
        """
        Select representative pixels for the provided raster dataset.

        The NaiveUnrasterizer simply chooses the n pixels that have the highest value.
        """
        # FIXME: Allow for multiple bands.
        band = raster_data.read()[0]
        sorted_pixels = self._sort_pixels(band)

        self._selected_indexes = list(range(0, self.n_pixels))
        self.selected_pixels = sorted_pixels[self._selected_indexes]
        self.selected_values = self._reassign_pixel_values(
            band=band,
            pixels=self.selected_pixels
        )
        self.selected_coords = self._get_coordinates(
            transform=raster_data.transform,
            pixels=self.selected_pixels
        )


class Unrasterizer(BaseUnrasterizer):
    """
    An implementation of the BaseUnrasterizer interface that insists on choosing far away points.

    If a given pixel is too close to another already selected pixel, do not select it.
    If a given pixel has a value below the Unrasterizer's threshold, do not select it.

    Intended to provide broader coverage of the area than the NaiveUnrasterizer.
    """

    def __init__(self, mask_width, threshold=1.0):
        """Inititalize an Unrasterizer."""
        super().__init__()
        self.mask_width = mask_width
        self.mask = None
        self.threshold = threshold
        self._raw_pixel_values = []

    def select_representative_pixels(self, raster_data, window=None):
        """Select representative pixels for the provided raster dataset."""
        if not window:
            window = rasterio.windows.Window(
                col_off=0, row_off=0, width=raster_data.width, height=raster_data.height
            )
        band = raster_data.read(window=window)[0]
        self._select_representative_pixels_from_band(
            band=band,
            transform=raster_data.transform,
            window=window
        )

    def _select_representative_pixels_from_band(self, band, transform, window=None):
        """
        Select representative pixels for the provided raster dataset within a single band.

        Used by the WindowedUnrasterizer to select pixels in parallel.
        """
        if not window:
            window = rasterio.windows.Window(
                col_off=0, row_off=0, width=band.shape[1], height=band.shape[0]
            )
        self.mask = band > self.threshold
        sorted_pixels = self._sort_pixels(band)

        for idx, pixel in enumerate(sorted_pixels):
            if self.mask[tuple(pixel)]:
                self._select_next_pixel(band, pixel, idx)

        self.selected_values = self._reassign_pixel_values(
            band=band,
            pixels=self.selected_pixels,
            raw_pixel_values=self._raw_pixel_values
        )
        self.selected_coords = self._get_coordinates(
            transform=transform,
            pixels=self.selected_pixels,
            col_offset=window.col_off,
            row_offset=window.row_off
        )

        return (
            self.selected_pixels,
            self.selected_values,
            self.selected_coords
        )

    def _select_next_pixel(self, band, pixel, idx):
        """Select the provided pixel as a representative point."""
        self._selected_indexes.append(idx)
        self.selected_pixels.append(pixel)

        row_slice, col_slice = self._get_pixel_window(
            pixel=pixel,
            width=self.mask_width,
            height=self.mask_width,
        )
        self.mask[row_slice, col_slice] = False
        # FIXME: Use self.mask_width / 2 for this window to avoid double-counting.
        window = band[row_slice, col_slice]
        self._raw_pixel_values.append(
            np.sum(
                window[window > 0.0],
                dtype=np.float32
            )
        )

    @staticmethod
    def _get_pixel_window(pixel, width, height):
        """Return the rows and columns of a rectangle centered at the given pixel."""
        # TODO: Use explicit slices.
        min_row = max(pixel[0] - width, 0)
        min_col = max(pixel[1] - height, 0)
        max_row = pixel[0] + width
        max_col = pixel[1] + height
        return slice(min_row, max_row), slice(min_col, max_col)

    @staticmethod
    def manhattan_distance(arr1, arr2):
        """Return the Manhattan (city-block) distance between two [row, column] arrays."""
        return np.sum(np.abs(arr1 - arr2))


class WindowedUnrasterizer(BaseUnrasterizer):
    """
    An implementation of the BaseUnrasterizer interface that operates over small areas.

    For large raster files, this class is much more memory efficient than the default Unrasterizer.
    """

    def __init__(self, mask_width, threshold=1.0):
        """Inititalize a WindowedUnrasterizer."""
        # TODO: Pass unrasterizer class as an argument, with settings determined by **kwargs.
        super().__init__()
        self.mask_width = mask_width
        self.mask = None
        self.threshold = threshold

    def select_representative_pixels(self, raster_data, window_shape=None, n_jobs=-1):
        """Select representative pixels for the provided raster dataset."""
        if not window_shape:
            window_shape = raster_data.block_shapes[0]

        windows = self._get_windows(raster_data, window_shape)
        bands = (raster_data.read(window=window)[0] for window in windows)
        transform = raster_data.transform

        if n_jobs < 0:
            n_jobs = pathos.helpers.cpu_count()

        with pathos.pools.ProcessPool(processes=n_jobs) as executor:
            results = executor.map(
                self.select_representative_pixels_in_window,
                bands,
                itertools.repeat(transform),
                windows
            )

        pixel_lists, value_lists, coord_lists = zip(*results)

        self.selected_pixels = [pixel for pixels in pixel_lists for pixel in pixels]
        self.selected_values = [value for values in value_lists for value in values]
        self.selected_coords = [coord for coords in coord_lists for coord in coords]

    def _get_windows(self, raster_data, window_shape):
        n_windows_x = math.ceil(raster_data.width / window_shape[0])
        n_windows_y = math.ceil(raster_data.height / window_shape[1])
        return [
            rasterio.windows.Window(
                col_off=i * window_shape[0],
                row_off=j * window_shape[1],
                width=window_shape[0],
                height=window_shape[1]
            )
            for i, j in itertools.product(range(n_windows_x), range(n_windows_y))
        ]

    def select_representative_pixels_in_window(self, band, transform, window):
        """Select representative pixels within a single window."""
        unrasterizer = Unrasterizer(mask_width=self.mask_width, threshold=self.threshold)
        pixels, values, coords = unrasterizer._select_representative_pixels_from_band(
            band=band,
            transform=transform,
            window=window
        )
        return pixels, values, coords
