# PostGIS Baselayers

PostGIS Baselayers is a web application that connects to a PostGIS database and lets you automatically download and import a selection of popular open vector datasets (Natural Earth, GADM, Geonames, etc) into the database. It comes bundled with a Docker environment and a PostGIS container to get up and running quickly.

The application and database works nicely as a standalone spatial database that you can run queries against, or you can load data from it directly using QGIS/GDAL tools.

![PostGIS Baselayers Homepage](docs/img/screenshot-home.png)

## Why

For a few years now I have had an assortment of different base layers lying around to help with making maps and visualizations, experimenting with PostGIS, and for various other spatial analysis tasks. Having these datasets just sitting around in all sorts of different formats was a hassle, and I decided to put some time into a framework that would organize them, make them available in a PostGIS environment, and that could be contributed to by others.

Installation of new datasets is a breeze with the installers, and having all the datasets in a single database lets you do all sort of fun queries across different datasets.

## Getting Started

### Quick Start

Clone the repository and build the containers with `docker-compose build` and start the service with `docker-compose up`. 

Once running, visit the management application in your browser at `http://localhost:8003/` and choose which datasets you want to install into the database. The container running the PostGIS database itself is exposed on port `35432` to avoid conflicts with other PostGIS instances that may be running on your machine.

### With an existing database

TODO

## Datasets

Vector datasets currently available in PostGIS Baselayers are currently:

* [Geonames](app/datasets/geonames/)
* [GADM](app/datasets/gadm/)
* [Koeppen-Geiger Climate Classifications](app/datasets/koeppengeiger/)
* [Example](app/datasets/example/)

If there is a dataset you'd like to see included, please create an issue in the issue tracker, or add it yourself and send a pull request.

## Issues

See the issue tracker for a list of issues and features.

## Technical Details

The database container is based on `mdillon/postgis`, and the application container uses `supervisord` to run the web-application and a Huey work queue for downloading and installing datasets in the background. 

## Contributing

Contributions are welcome, either on the application itself or by adding additional datasets to the index. Please contact me first if you have some ideas or would like to contribute.

### Datasets

The `datasets` subdirectory contains all the instructions to install each individual dataset. Each dataset subdirectory contains:

* A `Makefile` with `download`, `install`, and `clean` targets
* A `README.md` with documentation
* A `metadata.json` file with additional metadata.

See the [example](app/datasets/example/) dataset for a basic setup with some documentation that can be used as a template for a new dataset. The general idea is that the `download` target in the Makefile downloads the dataset from some location on the internet, and that the `install` target installs the dataset into a separate schema in the PostGIS database. The container has an assortment of tools installed (GDAL, psql) to help in this process.

See the [Makefile](app/datasets/example/Makefile) of the example dataset for an overview of how a dataset is downloaded and installed.

### Application

The application can be run in development mode by using Docker Compose and the `docker-compose-dev.yaml` compose file. This setup runs the application and the work queue in two different containers. Also, the application container uses Flask's development server instead of gunicorn for serving the web app.

