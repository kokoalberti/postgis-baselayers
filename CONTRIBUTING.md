# Contributing to PostGIS Baselayers

If you'd like to help out with this project, any help is greatly appreciated, no matter how big or small. There are a few areas that require work:

* Adding new datasets
* Improvements to the web application
* Documentation and code examples

Please contact me first if you'd like to help out with something.

## Adding new datasets

The `[./app/datasets/](app/datasets/)` subdirectory contains the scripts to install each individual dataset. Each dataset subdirectory contains:

* A `Makefile` with `download`, `install`, and `clean` targets.
* A `README.md` with documentation.
* A `metadata.json` file with additional metadata.

The web application contains a work queue which executes a `make` command when the user requests a particular dataset to be installed or removed from the database. The `Makefile` for that particular dataset is responsible for fullfilling the request.

See the [example](app/datasets/example/) dataset for a basic setup with some documentation that can be used as a template for a new dataset. The general idea is that the `download` target in the Makefile downloads the dataset from some location on the internet, and that the `install` target installs the dataset into a separate schema in the PostGIS database. The container has an assortment of tools installed (GDAL, psql) to help in this process.

See the [Makefile](app/datasets/example/Makefile) of the example dataset for an overview of how a dataset is downloaded and installed.

## Improvements to the web application

The application can be run in development mode by using Docker Compose and the `docker-compose-dev.yaml` compose file. This setup runs the application and the work queue in two different containers. Also, the application container uses Flask's development server instead of gunicorn for serving the web app.

The issue tracker contains some ideas on what can still be improved on the web application itself.

## Documentation and code examples

Each dataset has a `README.md` file which explains what data is in the dataset, where it comes from, and some usage examples. These docs are quite essential, and it would be nice if they are up to date and contain a variety of code examples of what you can do with the data in the dataset.
