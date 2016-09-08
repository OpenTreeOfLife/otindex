# otindex

A pyramid implementation of a treestore (and possibly general) index for Open Tree of Life.

In progress; not production ready. Currently set up to simply use a local postgresql database.

## Tech used in development

* python 2.7.10
* [pyramid](http://www.pylonsproject.org/) v 1.5.7
* [postgres](http://www.postgresql.org/) v 9.5.2
* [peyotl](https://github.com/OpenTreeOfLife/peyotl): for interacting with the opentree tree store

## Installation

**Setting up the database**
The `otindex/scripts` directory contains scripts for setting up the database
(creating tables, loading phylesystem studies, etc). See the [README](https://github.com/OpenTreeOfLife/otindex/blob/master/otindex/scripts/README.md) file in that directory for detailed setup information.

**Running the application**

Copy `development-example.ini` to `development.ini` and modify the database
line to point to your local copy of the postgres database. Then, in the top-level
directory, run:

```
$ pip install -r requirements.txt
$ python setup.py develop
$ pserve development.ini --reload
```

**Running tests**

In the ws-tests directory:

```
$ bash run_tests.sh
```

## Development notes

The top-level `dev_scripts` directory contains scripts for testing out new
features. Some implement peyotl functions, while others allow database testing
from the CLI without deploying pyramid. No promises that anything in that
directory works property.
