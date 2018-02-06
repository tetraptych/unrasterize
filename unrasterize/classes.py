"""Classes implementing methods to convert raster files to GeoJSON."""
import numpy as np


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
        total_selected = np.sum(raw_pixel_values, dtype=np.uint32)
        return [
            val * total / total_selected for val in raw_pixel_values
        ]

    @staticmethod
    def _get_coordinates(raster_data, pixels, row_offset=0, col_offset=0):
        return [
            raster_data.xy(
                row=row + row_offset,
                col=col + col_offset,
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
            raster_data=raster_data,
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
        """Inititalize a CleverUnrasterizer."""
        super().__init__()
        self.mask_width = mask_width
        self.mask = None
        self.threshold = threshold
        self._raw_pixel_values = []

    def select_representative_pixels(self, raster_data):
        """Select representative pixels for the provided raster dataset."""
        # FIXME: Allow for multiple bands.
        band = raster_data.read()[0]
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
            raster_data=raster_data,
            pixels=self.selected_pixels
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