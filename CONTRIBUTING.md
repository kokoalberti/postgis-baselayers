# Contributing to PostGIS Baselayers

If you'd like to help out with this project, any help is greatly appreciated, no matter how big or small. There are a few areas that require work:

* Adding new datasets
* Improvements to the web application
* Documentation and code examples

Please contact me first if you'd like to help out with something. I am currently overhauling some internals, so please check back in a few weeks for updates.

## Adding new datasets

The [`./app/datasets/`](app/datasets/) subdirectory contains the scripts to install layers in each individual dataset. Each dataset subdirectory contains:

* A `Makefile` for each layer in the dataset called `<layer>.make`, with an `install` and `uninstall` target.
* A `README.md` with documentation.
* A `metadata.json` file with additional metadata.

The web application contains a work queue which executes a `make` command when the user requests a particular dataset to be installed or removed from the database. The `Makefile` for that particular dataset is responsible for fullfilling the request. The install command is executed in a temporary directory as `make -f <layer>.make install`.

See the [example](app/datasets/example/) dataset for a basic setup with some documentation that can be used as a template for a new dataset. The general idea is that the `install` target in the Makefile downloads the dataset from some location on the internet and installs the dataset into a schema with the dataset name in the PostGIS database. The container has an assortment of command-line tools installed (GDAL, psql) to help in this process.

See the [airports.make](app/datasets/example/airports.make) in the example dataset for an overview of how a dataset is downloaded and installed.

## Improvements to the web application

The application can be run in development mode by using Docker Compose and the `docker-compose-dev.yaml` compose file. This setup runs the application and the work queue in two different containers. Also, the application container uses Flask's development server instead of gunicorn for serving the web app.

The issue tracker contains some ideas on what can still be improved on the web application itself. Please use that for feature requests.

## Documentation and code examples

Each dataset has a `README.md` file which explains what data is in the dataset, where it comes from, and some usage examples. These docs are quite essential, and it would be nice if they are up to date and contain a variety of code examples of what you can do with the data in the dataset.
