This directory contains scripts for setting up the database. If you have not
already set up postgresql and created a database, take a look at that section
at the end first.

## Configuration

First copy the template:

    `$ cp config.yml.example config.yml`

Then adjust the new file for your local settings:

* If Open Tree uses a database other than 'newoti', set this in config.yml.
* If Open Tree runs as a user other than 'pguser', set this in config.yml.
* If there is a database password, set this in config.yml. Otherwise,
  delete the password line
* Set location of taxonomy (usually a directory called 'ott' from an OTT
  distribution; the directory containing taxonomy.tsv and so on). The setup code
  can be run without a taxonomy; just put None.


## Creating tables

The preferred method is to allow pyramid to create tables based on `models.py`. You
probably did this if you followed the Installation instructions in the readme.
If you make a change to the models, you will want to re-create the tables. The
command is:

    $ initialize_otindex_db development.ini

Where `initialize_otindex_db` lives in the `bin` dir of your virtualenv.

If you want to test the database and don't want to deal with pyramid, you can
use `setup_db.py` with the -d flag to create the tables:

    $ python setup_db.py config.yml -d

The methods in `setup_db.py` call SQL `CREATE TABLE` directly using psycopg2.
These methods are leftover from early development of the database schema, and it
is possible that the CREATE statements may drift from the table definitions in
`models.py` over time. Use at your own risk (and if you get errors, change the
table defs here, not in models.py).

## Loading data

To load data into the database:

* `config.yml`: YAML file with database settings, including table names.
* `run_setup_scripts.sh`: bash script that runs the setup python files listed below. Takes as arguments a config file (required) and an integer (optional) that is the number of studies to load (default = load whole phylesystem)
* `setup_db.py`: creates DB tables if do not already exist; optionally deleting them all first
* `load_nexson.py`: loads the nexson files into the database and creates the JSON index
* `load_taxonomy.py`: loads the taxonomy files into the database
* `create\_otu\_table.py`: generates a csv file of otu-tree relationships and then loads this using the COPY command
* `test_db_selects.py`: does a few simple selects on study and tree table

To run all of the data load steps:
      `$ bash run_setup_scripts.sh config.yml {n}`

where n = number studies (optional; default is load all).

Or, you can run the steps individually:

  * setup: `$ python setup_db.py config.yml`. If you want to create tables, use
    the -d flag (noting that we recommend using the pyramid
    `initialize_otindex_db` script to create tables).
  * load nexsons: `$ python load_nexson.py config.yml`. You can use the `-n`
    flag to do an initial test with a small number of files.
  * load taxonomy: `$ python load_taxonomy.py config.yml`.
  * load the otu-tree table: `$ python create_otu_table.py config.yml`. Again,
    you can use `-n` to test a small number of input files.
  * run some simple tests: `$ python test_db_selects.py config.yml`

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

1. Create database for use by Open Tree.  If username, given here as 'pguser',
   does not exist on your system, either create it or specify a username that
   does exist (e.g. you).

    `$ createdb -Opguser -Eutf8 newoti`

# For interactive SQL

You'll want this for debugging.

    `$ psql -U pguser newoti`

were `pguser` is the postgres user and `newoti` is the database name.
