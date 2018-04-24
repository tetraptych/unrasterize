#!/usr/bin/env python
import setuptools


def _get_long_description():
    with open('README.md', 'r') as f:
        desc = f.read()
    return desc


def _get_version():
    with open('unrasterize/__init__.py') as f:
        for line in f:
            if line.find("__version__") >= 0:
                version = line.split("=")[1].strip()
                version = version.strip('"')
                version = version.strip("'")
                continue
    return version


setuptools.setup(
    name='unrasterize',
    version=_get_version(),
    description='A simple API for lossfully converting raster datasets to GeoJSON.',
    long_description=_get_long_description(),
    long_description_content_type='text/markdown',
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
    ],
    python_requires='>=3'
)
