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
    """A base interface from which other unrasterization classes inherit.

    This unrasterizer has no method to select representative pixels.

    Attributes
    ----------
    selected_pixels : list
        Selected pixels as (row, column) indexes.
    selected_values : list
        Raster values of selected pixels.
    selected_coords : list
        Coordinates of selected pixels.
    """

    def __init__(self):
        """Initialize a ``BaseUnrasterizer`` object."""
        self._selected_indexes = []
        self.selected_pixels = []
        self.selected_values = []
        self.selected_coords = []

    def select_representative_pixels(self, raster_data):
        """Select representative pixels for the provided raster dataset.

        Raises
        ------
        NotImplementedError
            This method is not implemented for the base unrasterizer class.
        """
        raise NotImplementedError

    def to_geojson(self, value_attribute_name='value', **extra):
        """Convert the selected points and values to GeoJSON.

        Parameters
        ----------
        value_attribute_name : str
            The attribute name corresponding to the aggregated pixel values in the ouput
            feature collection.
        extra : kwargs
            Keyword arguments passed to ``geojson.FeatureCollection(features, **extra)``.
            Useful when specifying a coordinate reference.

        Returns
        -------
        geojson.FeatureCollection
            A GeoJSON feature collection with the selected points as features with
            the single property ``value_attribute_name``.
        """
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
        """Convert the selected points and values to a ``geopandas.GeoDataFrame``.

        Parameters
        ----------
        value_attribute_name : str
            The attribute name corresponding to the aggregated pixel values in the ouput
            feature collection.
        extra : kwargs
            Keyword arguments passed to ``geojson.FeatureCollection(features, **extra)``.
            Useful when specifying a coordinate reference.

        Returns
        -------
        geopandas.GeoDataFrame
            A ``geopandas.GeoDataFrame`` with columns ``'geometry'`` and ``value_attribute_name``.
        """
        feature_collection = self.to_geojson(value_attribute_name, **extra)
        return gpd.GeoDataFrame.from_features(
            features=feature_collection['features'],
            crs=feature_collection.get('crs', None)
        )

    @staticmethod
    def _sort_pixels(band):
        """
        Sort a band, returning the row, column indexes in descending order by value.

        Parameters
        ----------
        band : np.ndarray
            Raster band in array format.

        Returns
        -------
        np.ndarray
            Array of shape ``(band.size, 2)`` corresponding to the indexes of pixels sorted by
            value (descending).
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
        """Adjust values of selected pixels so that their sum is preserved.

        Parameters
        ----------
        band : np.ndarray
            Raster band in array format.
        pixels : array-like
            Iterable of selected pixels (as a list of tuples or two-element arrays).
        raw_pixel_values : list, optional
            The values corresponding to ``pixels`` before adjustment.
            The values are inferred from ``band`` if missing.

        Returns
        -------
        list
            List of values of the same size as ``pixels`` with the same sum as ``band``.
        """
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
        """
        Get the geographic coordinates for a list of pixels.

        Parameters
        ----------
        transform : affine.Affine
            An affine transformation for the provided raster data.
        pixels : array-like
            Iterable of selected pixels (as a list of tuples or two-element arrays).
        row_offset, col_offset : int
            Integers indicating the offset to be supplied to ``transform``.
            Particularly useful when reading raster datasets window-by-window.

        Returns
        -------
        list
            A list of geographic coordinates for each input pixel.
        """
        return [
            rasterio.transform.xy(
                transform=transform,
                rows=row + row_offset,
                cols=col + col_offset,
            )
            for row, col in pixels
        ]


class NaiveUnrasterizer(BaseUnrasterizer):
    """A naive implementation of the ``BaseUnrasterizer`` interface.

    Always chooses the pixels with the highest values. These pixels may be close together.

    Parameters
    ----------
    n_pixels : int
        Number of pixels to select from the provided raster data.

    Attributes
    ----------
    selected_pixels : list
        Selected pixels as (row, column) indexes.
    selected_values : list
        Raster values of selected pixels.
    selected_coords : list
        Coordinates of selected pixels.
    """

    def __init__(self, n_pixels):
        """Initialize a NaiveUnrasterizer object."""
        super().__init__()
        self.n_pixels = n_pixels

    def select_representative_pixels(self, raster_data):
        """Select representative pixels for the provided raster dataset.

        The ``NaiveUnrasterizer`` simply chooses the ``self.n_pixels`` that have the highest values.
        Rather than returning values, this method sets the corresponding instance attributes.

        Parameters
        ----------
        raster_data : rasterio.io.DatasetReader
            An open raster file.
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
    An implementation of the ``BaseUnrasterizer`` interface that insists on choosing distant points.

    If a given pixel is too close to another already selected pixel, do not select it.
    If a given pixel has a value below ``threshold``, do not select it.

    Intended to provide broader coverage of the area than the ``NaiveUnrasterizer``.

    Parameters
    ----------
    mask_width : int
        The minimum number of non-selected pixels between adjacent selected pixels.
    threshold : float
        The minimum value required for a pixel to be selected.

    Attributes
    ----------
    mask : array-like
        Boolean array indicating what pixels remain that can still be chosen.
        Pixels within ``mask_width`` of already selected pixels and pixels that fall below
        ``threshold`` will have ``False`` in the corresponding array entry.
    selected_pixels : list
        Selected pixels as (row, column) indexes.
    selected_values : list
        Raster values of selected pixels.
    selected_coords : list
        Coordinates of selected pixels.
    """

    def __init__(self, mask_width, threshold=1.0):
        """Inititalize an Unrasterizer."""
        super().__init__()
        self.mask_width = mask_width
        self.mask = None
        self.threshold = threshold
        self._raw_pixel_values = []

    def select_representative_pixels(self, raster_data, window=None):
        """Select representative pixels for the provided raster dataset.

        Rather than returning values, this method sets the corresponding instance attributes.

        Parameters
        ----------
        raster_data : rasterio.io.DatasetReader
            An open raster file.
        window : rasterio.windows.Window, optional
            A window from which to select the pixels.
        """
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
        """Select representative pixels for the provided raster dataset within a single band.

        Used by the ``WindowedUnrasterizer`` to select pixels in parallel.

        Parameters
        ----------
        band : np.ndarray
            Raster band in array format.
        transform : affine.Affine
            An affine transformation for the provided raster data.
        window: rasterio.windows.Window, optional
            A window from which to select the pixels.
            Used to keep track of row and column offsets.

        Returns
        -------
        (selected_pixels, selected_values, selected_coords) tuple
            A tuple of three array-like objects corresponding to the instance attributes.
        """
        if not window:
            window = rasterio.windows.Window(
                col_off=0, row_off=0, width=band.shape[1], height=band.shape[0]
            )
        # Only select pixels with values above the threshold.
        self.mask = band > self.threshold
        sorted_pixels = self._sort_pixels(band)

        for idx, pixel in enumerate(sorted_pixels):
            # For each potential selection, select it if it has not yet been masked.
            # In addition, add nearby pixels to the mask.
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
        """Select the provided pixel as a representative point.

        Add nearby pixels to the mask to avoid selecting them later.
        Append the point information to the instance attributes.
        """
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
    """An implementation of the ``BaseUnrasterizer`` interface that operates over small areas at a time.

    This class is orders of magnitude more memory efficient than the default ``Unrasterizer`` class
    and so is the recommended class for working with large raster files.

    Selections are made in parallel using the ``pathos`` library.

    Parameters
    ----------
    mask_width : int
        The minimum number of non-selected pixels between adjacent selected pixels.
    threshold : float
        The minimum value required for a pixel to be selected.

    Attributes
    ----------
    mask : array-like
        Boolean array indicating what pixels remain that can still be chosen.
        Pixels within ``mask_width`` of already selected pixels and pixels that fall below
        ``threshold`` will have ``False`` in the corresponding array entry.
    selected_pixels : list
        Selected pixels as (row, column) indexes.
    selected_values : list
        Raster values of selected pixels.
    selected_coords : list
        Coordinates of selected pixels.
    """

    def __init__(self, mask_width, threshold=1.0):
        """Inititalize a WindowedUnrasterizer."""
        # TODO: Pass unrasterizer class as an argument, with settings determined by **kwargs.
        super().__init__()
        self.mask_width = mask_width
        self.mask = None
        self.threshold = threshold

    def select_representative_pixels(self, raster_data, window_shape=None, n_jobs=-1):
        """Select representative pixels for the provided raster dataset.

        The entire band is never held in memory. Each window is treated as its own independent band.
        Pixels are selected within each window, then recombined into a single array.

        Rather than returning values, this method sets the corresponding instance attributes.

        Parameters
        ----------
        raster_data : rasterio.io.DatasetReader
            An open raster file.
        window_shape: 2-element tuple, optional
            A window shape in the format (n_rows, n_columns).
            Defaults to the block shape of ``raster_data``.
        n_jobs: int, optional
            The number of processors to use.
            Defaults to the maximum number of available CPUs.
        """
        if not window_shape:
            window_shape = raster_data.block_shapes[0]

        if n_jobs < 0:
            n_jobs = pathos.helpers.cpu_count()

        windows = self._get_windows(raster_data, window_shape)
        bands = (raster_data.read(window=window)[0] for window in windows)
        transform = raster_data.transform

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
        """
        Subdivide the provided raster data into a list of windows.

        Parameters
        ----------
        raster_data : rasterio.io.DatasetReader
            An open raster file.
        window_shape : 2-element tuple
            A window shape in the format (n_rows, n_columns).

        Returns
        -------
        list(rasterio.windows.Window)
            A list of windows in row-major order.
        """
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
        """Select representative pixels within a single window using an ``Unrasterizer`` object.

        Parameters
        ----------
        band : np.ndarray
            Raster band in array format.
        transform : affine.Affine
            An affine transformation for the provided raster data.
        window : rasterio.windows.Window
            A window from which to select the pixels.
            Used to keep track of row and column offsets.
        """
        unrasterizer = Unrasterizer(mask_width=self.mask_width, threshold=self.threshold)
        pixels, values, coords = unrasterizer._select_representative_pixels_from_band(
            band=band,
            transform=transform,
            window=window
        )
        return pixels, values, coords
