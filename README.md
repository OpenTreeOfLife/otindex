# otindex

A pyramid implementation of a treestore (and possibly general) index for Open Tree of Life.

In progress; not production ready. Currently set up to simply use a local postgresql database.

## Tech used in development

* python 2.7.10
* [pyramid](http://www.pylonsproject.org/) v 1.5.7
* [postgres](http://www.postgresql.org/) v 9.5.2
* [peyotl](https://github.com/OpenTreeOfLife/peyotl): for interacting with the opentree tree store

## Installation

**Install otindex and set up the database tables**

You probably want to be using a virtualenv.

```
$ pip install -r requirements.txt
$ python setup.py develop
$ initialize_otindex_db development.ini
```
where `initialize_otindex_db` is in the `bin` directory of your virtualenv.
This last step creates the database tables defined in `models.py`. It drops any
existing tables and re-creates them.

**Load data into the database**
The `otindex/scripts` directory contains scripts for loading data into the
database. See the
[README](https://github.com/OpenTreeOfLife/otindex/blob/master/otindex/scripts/README.md)
file in that directory for detailed setup information.

**Running the application**

Copy `development-example.ini` to `development.ini` and modify the database
line to point to your local copy of the postgres database. Then, in the top-level
directory, run:

    $ pserve development.ini --reload

You should now be able to access the methods on `http://0.0.0.0:6543`.

**Running tests**

See TESTING.md in this repo.

## Development notes

The top-level `dev_scripts` directory contains scripts for testing out new
features. Some implement peyotl functions, while others allow database testing
from the CLI without deploying pyramid. No promises that anything in that
directory works property.
