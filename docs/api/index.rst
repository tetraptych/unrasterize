Unrasterize API
===================
The following classes exist to convert raster data to GeoJSON.

For large raster files, the `WindowedUnrasterizer <unrasterize.WindowedUnrasterizer.html>`_ is the most memory efficient, with the caveat that it may select some points from adjacent windows that are very close together.


Classes
-------
.. toctree::

    unrasterize.BaseUnrasterizer
    unrasterize.Unrasterizer
    unrasterize.WindowedUnrasterizer
