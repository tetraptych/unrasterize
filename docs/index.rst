===========
Unrasterize
===========

Motivation
==========
Raster data formats have become increasingly popular to represent global population density (see, for example, CIESIN's `Gridded Population of the World <http://sedac.ciesin.columbia.edu/data/collection/gpw-v4>`_). But the sheer number of pixels can make working with raster data difficult for certain use cases, especially in live applications where calculations are performed on the fly.

Enter ``unrasterize``, a lightweight package to extract representative population points from raster data. The library returns points in vector format (i.e., GeoJSON), selecting certain pixels as "representative" and aggregating nearby population values to preserve the total population.

For a concrete example, consider `Encompass <http://github.com/bayesimpact/encompass>`_, a tool used to measure spatial access to critical social services. Measuring the driving time between every raster pixel and every service provider is computationally infeasible. Unrasterizing the data yields a manageable number of points and allows the massive pairwise distance computation to terminate before the sun becomes a red giant.

Note that some loss of fidelity is inevitable. In fact, that's the point.

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
