# ottreeindex

A pyramid implementation of a treestore (and possibly general) index for Open Tree of Life.

In progress; not production ready. Currently set up to use a local postgresql database.

## Tech and versions used in development

* python 2.7.10
* [pyramid](http://www.pylonsproject.org/) v 1.5.7
* [postgres](http://www.postgresql.org/) v 9.5.2
* [peyotl](https://github.com/OpenTreeOfLife/peyotl): for interacting with the opentree tree store

## Installation

**Setting up the database**
The `ottreeindex/scripts` directory contains scripts for setting up the database
(creating tables, loading phylesystem studies, etc). See the [README](https://github.com/OpenTreeOfLife/ottreeindex/blob/master/ottreeindex/scripts/README.md) file in that directory for setup information.

**Running the application**

Copy `development-example.ini` to `development.ini` and modify the database line to point to your local copy of the postgres database.

Then, in the top-level directory, run:

```
$ pserve development.ini --reload
```

**Running tests**

In the ws-tests directory:

```
$ bash run_tests.sh
```
