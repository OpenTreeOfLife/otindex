## Loading data into local database

These instructions assumes you are doing development setup on your local
machine. If you are wanting to deploy otindex on a server, look at the [ansible
deployment](https://github.com/OpenTreeOfLife/otindex_ansible).

This directory contains scripts for setting up the database. If you have not
already set up postgresql and created a database, take a look at that section
at the end first. Then, follow the configuration and installation instructions
in the top-level README.

## Creating tables

The preferred method is to allow pyramid to create tables based on `models.py`.
You probably did this if you followed the Installation instructions in the
readme.

If you want to test the database and don't want to deal with pyramid, you can
use `setup_db.py` with the -d flag to drop and re-create the tables:

    $ python setup_db.py <config> -d

The methods in `setup_db.py` call SQL `CREATE TABLE` directly using psycopg2.
These methods are leftover from early development of the database schema, and it
is possible that the CREATE statements may drift from the table definitions in
`models.py` over time. Use at your own risk (and if you get errors, change the
table defs in `setup_db.py` to match `models.py`, not the other way around).

## Loading data

To **run all of the data load steps**:

    $ bash run_setup_scripts.sh <config> {n}

where n = number studies (optional; default is load all). Note that this method
only clears existing tables, it does not re-create them.

OR

To **run the steps individually** (assuming tables already created), where
`<config>` is the path to `development.ini`:

1. Load phylesystem. You can use the `-n` flag to do an initial test with a small number of files.

    `$ python load_nexson.py <config>`

1. Generate the taxonomy files. Given the size of OTT, we create extract the
required data into csv files and load these using the postgresql `copy` command
rather than doing millions of inserts. The files created are `ott.csv`
(taxonomy), `synonyms.csv` (synonyms), and `tree_otu_assoc.csv` (holds mapping
between trees and otus). The location of OTT is specified in the peyotl config.

    `$ python generate_taxonomy_files.py <config>`

1. Load the taxonomy files. Again, you can use `-n` to test a small number of input
files (noting that the whole taxonomy always gets loaded).

    `$ python create_otu_table.py <config>`

1. Run some simple tests:

    `$ python test_db_selects.py <config>`

# Postgres setup

These are notes from early development. Do not run the following sequence
blindly; it is only a template.
This was tested on OS X 10.9.

1. Install postgres.  There are other ways to do this.

    `$ brew install postgres`

1. Arrange for postgres to start after reboots.  The .plist file references `/usr/local/var/postgres`.
   You will probably have to change the version number in the path.
   This step is completely optional; you can start it manually with `postgres -D /usr/local/var/postgres` if you prefer.

    `$ mkdir -p ~/Library/LaunchAgents
    $ ln -sfv /usr/local/opt/postgresql/*.plist ~/Library/LaunchAgents`

1. Initialize the directory where postgres keeps its databases.
   (Do this only if the directory does not exist or is empty.)

   `$ initdb /usr/local/var/postgres`

1. Launch postgres DBMS server in background.

    `$ launchctl load ~/Library/LaunchAgents/homebrew.mxcl.postgresql.plist`

1. Create database for use by Open Tree.  If username, given here as 'postgres',
   does not exist on your system, either create it or specify a username that
   does exist (e.g. you). If you plan to export the database to a server, then
   you need to use username=postgres and database name = otindex.

    `$ createdb -Opostgres -Eutf8 otindex`

1. Create a non-priviledged database user:

    `$ createuser opentree -D -S -P`

1. Connect to the database with the superuser account and grant permissions to
   the new user:

   ` $ psql otindex`
   ` otindex=# GRANT ALL ON DATABASE otindex TO opentree;`

# For interactive SQL

You'll want this for debugging.

    `$ psql -U postgres otindex`

were `postgres` is the postgres user and `otindex` is the database name.
