# PostGIS Baselayers

PostGIS Baselayers is a PostGIS Docker container with a lightweight web-interface which lets you - with the click of a button - download and import an assortment of public vector datasets into the database. It works nicely as a standalone spatial database that you can run queries against, or you can load data from it directly using QGIS/GDAL tools.

## Why

For a few years now I have had an assortment of different base layers lying around to help with making maps and visualizations, experimenting with PostGIS, and for various other spatial analysis tasks. Having these datasets just lying around in all sorts of different formats was becoming a bit annoying, and I decided to put some time into a framework that would organize this data and that could be contributed to by others.

## Getting Started

### Quick Start

Clone the repository and build the containers with `docker-compose build` and start the service with `docker-compose up`. 

Once running, visit the management application in your browser at `http://localhost:8003/` and choose which datasets you want to install into the database. The PostGIS database itself is exposed on port `35432`.

## Datasets

Vector datasets currently available in PostGIS Baselayers are:

* [Geonames](app/datasets/geonames/)
* [GADM](app/datasets/gadm/)
* [Koeppen-Geiger Climate Classifications](app/datasets/koeppengeiger/)
* [Example](app/datasets/example/)

If there is a dataset you'd like to see included, please create an issue in the issue tracker, or add it yourself and send a pull request.

## Issues

See the issue tracker for a list of issues and TODOs. This is still pretty much a work in progress, I hope in the future it can grow into something other people use as well.

## Technical Details

The container is based on `mdillon/postgis` and uses `supervisord` to run PostGIS, the Flask web-application, and a Huey work queue for downloading datasets and doing other tasks in the background.

While it's not necessarily best practice to ship multiple services in a single container, I've decided to do so anyway to keep everything nice and compact. This way you won't have to use Docker Compose if you don't want to, and it'll be easy to integrate the PostGIS Baselayers container as-is into other applications without having to configure the database, webapp, and worker individually. Just start up the container, install the datasets you want, and you're good to go. This needs to be as simple as possible.

## Contributing

Contributions are welcome, either on the application itself or by adding additional datasets to the index. Please contact me first before sending a PR.

### Datasets

The `datasets` subdirectory contains all the instructions to install each individual dataset. Each dataset subdirectory contains:

* A `Makefile` with `download`, `install`, and `clean` targets
* A `README.md` with documentation
* A `metadata.json` file with additional metadata.

See the [example](app/datasets/example/) dataset for a basic setup with some documentation that can be used as a template for a new dataset.

The general idea is that the `download` target in the Makefile downloads the dataset from some location on the internet, and that the `install` target installs the dataset into a separate schema in the PostGIS database. The container has an assortment of geospatial tools installed to help in this process.

### Application

The application can be run in development mode by using Docker Compose and the `docker-compose-dev.yaml` compose file.

