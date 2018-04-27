Usage
=====

Algorithm walkthrough
---------------------

Let's walk through the algorithm behind the default ``Unrasterizer`` class. The basic use pattern is as follows: ::

    u = Unrasterizer(mask_width=3, threshold=0.5)
    representative_points = u.select_representative_pixels(raster_data)

``mask_width`` indicates minimum number of non-selected pixels between adjacent selected pixels.

``threshold`` indicates the minimum value required for a pixel to be selected. Measured in the same units as value (often population per pixel).

First, all pixels with value below the given threshold will be ignored. The remaining pixels are sorted according to their values and considered for selection one by one.

After each point is selected, all points within a square of radius ``mask_width`` around the newly chosen point are masked and removed from further consideration. This process continues until every point is either selected or part of the mask.

The ``Unrasterizer`` class performs this selection process on the entire raster file, while the ``WindowedUnrasterizer`` applies the same process across each individual raster block and combines the results into a single array of selected pixels.

Demonstration
-------------

..  image:: https://github.com/tetraptych/unrasterize/blob/master/docs/img/unrasterizer.gif?raw=true

Here, the initial red triangle in the west represents pixels that fall below the threshold.

The purple point indicates the point with the highest value. It is chosen first.

Then, all points within a square of radius ``mask_width`` are added to the mask (moving from turquoise to orange to red). These points will never be selected going forward.

Next, the remaining (turquoise) point with the highest value is selected and the pixels around it are masked.

Examples
--------
For an example of ``unrasterize`` in action, see `this Jupyter notebook <https://github.com/tetraptych/unrasterize/blob/master/examples/basic_unrasterizer_usage.ipynb>`_.
