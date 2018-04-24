# Unrasterize [![PyPI version](https://badge.fury.io/py/unrasterize.svg)](https://badge.fury.io/py/unrasterize) [![Build Status](https://travis-ci.org/tetraptych/unrasterize.svg?branch=master)](https://travis-ci.org/tetraptych/unrasterize) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Unrasterize is a Python library for converting raster datasets into GeoJSON objects by selecting representative points based on their pixel values. The conversion process results in less granular data with dramatically reduced file sizes for use in other applications that accept GeoJSON inputs.

The inspiration and original use case for this library is the 100m resolution population data provided by [WorldPop](http://www.worldpop.org.uk/). This is also the source of the files in the `data` directory used by the unit tests.

## Installation

`unrasterize` is available on [PyPI](https://pypi.python.org/pypi/unrasterize) and can be installed via the command `pip install unrasterize`.

`rasterio`, a depedency of `unrasterize`, may require the installation of additional GIS-specific tools outside of `pip`. Refer to the [Dockerfile](Dockerfile) for a list of these tools and how to install them.

## Sample output

![Representative points for France created using WorldPop raster data](https://farm5.staticflickr.com/4708/39370187915_693f694b79_z_d.jpg "Representative points for France created using WorldPop raster data")
