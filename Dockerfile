FROM jupyter/scipy-notebook:latest

EXPOSE 8888
ENV NODE_ENV development

USER root

# Install libraries used by geopandas
RUN apt-get -qq update

RUN apt-get -qq install \
    wget \
    build-essential \
    curl \
    zip \
    unzip \
    man \
    --fix-missing \
    > /dev/null

RUN apt-get -qq install \
    libgeos-dev \
    libgdal-dev \
    libspatialindex-dev \
    gdal-bin \
    python-gdal \
    --fix-missing \
    > /dev/null

USER jovyan

WORKDIR /home/jovyan/work
RUN cd /home/jovyan/work

COPY requirements.txt .
RUN pip -q install -r requirements.txt
