This directory contains scripts for setting up the database from the command line (or from within pyramid)

# Files:

For command-line setup (for testing the database from outside pyramid):
* config.yml: YAML file with database settings, including table names.
* setup_db.py: creates DB tables if do not already exist; optionally deleting them all first
* load_nexson.py: loads the nexson files into the database and creates the JSON index
* create_otu_table.py: generates a csv file of otu-tree relationships and then loads this using the COPY command

Pyramid setup:
* initializedb.py: the pyramid file for iniatializing the database

# Setting up the DB on the command-line

1. `$ cp config.yml.example config.yml` and adjust the new file for your local settings
* setup: `$ python setup_db.py config.yml`
* load nexsons: `$ python load_nexson.py config.yml`. You can use the `-n` flag to do an initial test with a small number of files.
* load the otu-tree table: `$ python create_otu_table.py config.yml`. Again, you can use `-n` to test a small number of input files.
* test setup: `$ nosetests test_db_setup.py -v`
