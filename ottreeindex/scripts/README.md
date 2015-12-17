This directory contains scripts for setting up the database from the command line (or from within pyramid)

# Files:

For command-line setup (for testing not from within pyramid):
* config.yml: YAML file with database settings, including table names.
* setup_db.py: deletes and existing tables and re-creates them
* load_nexson.py: loads the nexson files into the database and creates the JSON index
* create_otu_table.py: generates a csv file of otu-tree relationships and then loads this using the COPY command

Pyramid setup:
* initializedb.py: the pyramid file for iniatializign the database

# Setting up the DB on the command-line

1. `$ cp config.yml.example config.yml` and adjust the new file for your local settings
* setup: `$ setup_db.py config.yml`
* load nexsons: `$ load_nexson.py config.yml`. You can use the `-n` flag to do an initial test with a small number of files.
* load the otu-tree table: `$ create_otu_table.py config.yml`. Again, you can use `-n` to test a small number of input files.
* test setup: `$ nosetests test_db_setup.py -v`
