# Unrasterize [![Build Status](https://travis-ci.org/tetraptych/unrasterize.svg?branch=master)](https://travis-ci.org/tetraptych/unrasterize) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Unrasterize is a Python library for converting raster datasets into GeoJSON objects by selecting representative points based on their pixel values. The conversion process results in less granular data with dramatically reduced file sizes for use in other applications that accept GeoJSON inputs.

The inspiration and original use case for this library is the 100m resolution population data provided by [WorldPop](http://www.worldpop.org.uk/). This is also the source of the files in the `data/` directory used by the unit tests.

## Example output

![30,000 representative points for Tanzania](https://farm5.staticflickr.com/4604/39273432645_ba8e69efba_z_d.jpg "30,000 representative points for Tanzania (sized by population)")
