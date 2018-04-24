===========
Unrasterize
===========

Motivation
==========
Raster data formats have become increasingly popular to represent global population density (see, for example, CIESIN's `Gridded Population of the World <http://sedac.ciesin.columbia.edu/data/collection/gpw-v4>`_). But the sheer number of pixels can make working with raster data difficult for certain use cases.

Enter ``unrasterize``, a lightweight package to extract representative population points from raster data. The resulting points exist in vector format (i.e., GeoJSON) and can be used by downstream applications.

Sample Output
=============
.. image:: https://farm5.staticflickr.com/4708/39370187915_693f694b79_z_d.jpg

Contents
=================

.. toctree::
    :maxdepth: 2

    usage
    api/index
    contributing


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
