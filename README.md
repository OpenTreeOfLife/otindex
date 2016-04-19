# ottreeindex

A pyramid implementation of a treestore (and possibly general) index for Open Tree of Life.

In progress; not production ready. Currently set up to use a local postgresql database.

## Installation

**Setting up the database**
The ottreeindex/scripts directory contains scripts for setting up the database
(creating tables, loading phylesystem studies, etc). See the [README](https://github.com/OpenTreeOfLife/ottreeindex/blob/master/ottreeindex/scripts/README.md) file in that directory for setup information.

**Running the application**

Copy `development-example.ini` to `development.ini` and moodify the database line to point to your local copy of the postgres database.

Then, in the top-level directory, run:

```
$ pserve development.ini --reload
```

**Running tests**

In the ws-tests directory:

```
$ bash run_tests.sh
```
