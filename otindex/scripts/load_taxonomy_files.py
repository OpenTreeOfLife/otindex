# Imports ott.csv, synonyms.csv, tree_otu_assoc.csv into the database
# Assumes database already set up. This happends either in initializedb.py
#   if running pyramid app or setup_db.py for testing (both in
#   this same directory)

import datetime as dt
import argparse
import psycopg2 as psy
import os

# other database functions
import setup_db

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='load ott into postgres')
    parser.add_argument('configfile',
        help='path to the development.ini file'
        )
    parser.add_argument('files_dir',
        help='path to the directory holding the csv files'
        )
    args = parser.parse_args()

    try:
        # read config variables
        config_obj = setup_db.read_config(args.configfile)
        connection, cursor = setup_db.connect(config_obj)

        # import the csv files into the tables
        starttime = dt.datetime.now()
        print "Importing taxonomy files"

        fullpath = os.path.abspath(args.files_dir)
        # taxonomy: ott.csv
        ott_filename = os.path.join(fullpath,'ott.csv')
        TAXONOMYTABLE = config_obj.get('database_tables','otttable')
        setup_db.import_csv_file(connection,cursor,TAXONOMYTABLE,ott_filename)

        # synonyms: synonyms.csv
        synonym_filename = os.path.join(fullpath,'synonyms.csv')
        SYNONYMTABLE = config_obj.get('database_tables','synonymtable')
        setup_db.import_csv_file(connection,cursor,SYNONYMTABLE,synonym_filename)

        # tree-otu mapping: tree_otu_assoc.csv
        tree_otu_filename = os.path.join(fullpath,'tree_otu_assoc.csv')
        TREEOTUTABLE = config_obj.get('database_tables','treeotutable')
        setup_db.import_csv_file(connection,cursor,TREEOTUTABLE,tree_otu_filename)

        endtime = dt.datetime.now()
        print "OTT file load time: ",endtime - starttime
        connection.close()

    except psy.Error as e:
        print e.pgerror
