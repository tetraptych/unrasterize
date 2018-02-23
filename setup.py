#!/usr/bin/env python
import setuptools

setuptools.setup(
    name='unrasterize',
    version='0.1.0',
    description='A simple API for lossfully converting raster datasets to GeoJSON.',
    url='http://github.com/tetraptych/unrasterize',
    keywords=['geospatial', 'geo', 'raster', 'gdal'],
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: GIS',
    ],
    author='Brian Lewis',
    author_email='brianburkelewis@gmail.com',
    license='MIT',
    packages=['unrasterize'],
    install_requires=[
        'rasterio>=1.0a12',
        'pathos>=0.2.0',
        'numpy>=1.8.0',
        'geojson>=1.3.0',
        'geopandas>=0.2.0'
    ]
)
