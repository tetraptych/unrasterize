FROM jupyter/scipy-notebook:latest

EXPOSE 8888
ENV NODE_ENV development

USER root

# Install libraries used by geopandas
RUN apt-get -qq update

RUN apt-get install -y \
    wget \
    build-essential \
    curl \
    zip \
    unzip \
    man \
    --fix-missing

RUN apt-get install -y \
    libgeos-dev \
    libgdal-dev \
    libspatialindex-dev \
    gdal-bin \
    python-gdal \
    --fix-missing

USER jovyan

WORKDIR /home/jovyan/work
RUN cd /home/jovyan/work

COPY requirements.txt .
RUN pip install -r requirements.txt
