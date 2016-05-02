This directory contains scripts for setting up the database from the command line (or from within pyramid). 

# Files:

For command-line setup (for testing the database from outside pyramid):

* `config.yml`: YAML file with database settings, including table names.
* `run_setup_scripts.sh`: bash scripts that runs the following python files:
  * `setup_db.py`: creates DB tables if do not already exist; optionally deleting them all first
  * `load_nexson.py`: loads the nexson files into the database and creates the JSON index
  * `create\_otu\_table.py`: generates a csv file of otu-tree relationships and then loads this using the COPY command
  * `test_db_selects.py`: does a few simple selects on study and tree table

For use with pyramid:

* initializedb.py: the pyramid file for initializing the database. You should not need to edit this.


# Setting up the database on the command line

## Postgres setup

Do not run the following sequence blindly; it is only a template.
This was tested on OS X 10.9.

1. Install postgres.  There are other ways to do this.

    `$ brew install postgres`

1. Arrange for postgres to start after reboots.  The .plist file references /usr/local/var/postgres.
   You will probably  have to change the version number in the path.
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

## Configuration

First copy the template:

    `$ cp config.yml.example config.yml`

Then adjust the new file for your local settings:

* If Open Tree uses a database other than 'newoti', set this in config.yml.
* If Open Tree runs as a user other than 'pguser', set this in config.yml.
* Set location of taxonomy (usually a directory called 'ott' from an OTT distribution;
  the directory containing taxonomy.tsv and so on).  The setup code
  can be run without a taxonomy; just put None.


## Initialize and load the database

* setup: `$ python setup_db.py config.yml`
* load nexsons: `$ python load_nexson.py config.yml`. You can use the `-n` flag to do an initial test with a small number of files.
* load the otu-tree table: `$ python create_otu_table.py config.yml`. Again, you can use `-n` to test a small number of input files.
* test setup: `$ nosetests test_db_setup.py -v`


# For interactive SQL

You'll want this for debugging.

    psql -U pguser newoti
