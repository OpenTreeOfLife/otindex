# Sets up the postgres database for future nexson import
# Deletes existing tables and re-creates them
# Also includes some utility functions

# Changes to table structure must be replicated in ../models.py

import argparse
import yaml
import psycopg2 as psy
import simplejson as json
#import logging
import pdb

def clear_gin_index(connection,cursor,config_dict):
    print 'clearing GIN indexes'

    # study table
    STUDYGININDEX=config_dict['studyginindex']
    sqlstring = "DROP INDEX IF EXISTS {indexname};".format(indexname=STUDYGININDEX)
    cursor.execute(sqlstring)
    # tree table
    TREEGININDEX=config_dict['treeginindex']
    sqlstring = "DROP INDEX IF EXISTS {indexname};".format(indexname=TREEGININDEX)
    cursor.execute(sqlstring)

    connection.commit()

def clear_single_table(connection,cursor,tablename):
    print 'clearing table',tablename
    sqlstring=('TRUNCATE {t} CASCADE;').format(t=tablename)
    cursor.execute(sqlstring)

def clear_tables(connection,cursor,config_dict):
    print 'clearing tables'
    # tree linked to study via foreign key, so cascade removes both
    tabledict = config_dict['tables']
    for table in tabledict:
        name = tabledict[table]
        sqlstring=('TRUNCATE {t} CASCADE;'
            .format(t=name)
        )
        #print '  SQL: ',cursor.mogrify(sqlstring)
        cursor.execute(sqlstring)

def connect(config_dict):
    conn = cursor = None  # not sure of exception intent
    try:
        DBNAME = config_dict['connection_info']['dbname']
        USER = config_dict['connection_info']['user']
        connectionstring=("dbname={dbname} "
            "user={dbuser}"
            .format(dbname=DBNAME,dbuser=USER)
            )
        conn = psy.connect(connectionstring)
        cursor = conn.cursor()
    except KeyboardInterrupt:
        print "Shutdown requested because could not connect to DB"
    except psy.Error as e:
        print e
        # print e.pgerror
    return (conn,cursor)

def create_table(connection,cursor,tablename,tablestring):
    try:
        if (table_exists(cursor,tablename)):
            print '{table} table exists'.format(table=tablename)
        else:
            print 'creating table',tablename
            cursor.execute(tablestring)
            connection.commit()
    except psy.Error as e:
        print 'Error creating table {name}'.format(name=tablename)
        print e.pgerror

# Function to create all database tables
# Any changes made to the tablestring should also be reflected in
# ottreeindex/models.py
def create_all_tables(connection,cursor,config_dict):
    # study table
    STUDYTABLE = config_dict['tables']['studytable']
    tablestring = ('CREATE TABLE {tablename} '
        '(id text PRIMARY KEY, '
        'year integer, '
        'data jsonb);'
        .format(tablename=STUDYTABLE)
        )
    create_table(connection,cursor,STUDYTABLE,tablestring)

    # tree table
    TREETABLE = config_dict['tables']['treetable']
    tablestring = ('CREATE TABLE {tablename} '
        '(id serial PRIMARY KEY, '
        'tree_id text NOT NULL, '
        'study_id text REFERENCES study (id) ON DELETE CASCADE, '
        'treebase_id text, '
        'ntips Integer, '
        'proposed boolean, '
        'data jsonb, '
        'UNIQUE (tree_id,study_id));'
        .format(tablename=TREETABLE)
        )
    create_table(connection,cursor,TREETABLE,tablestring)

    # curator table
    CURATORTABLE = config_dict['tables']['curatortable']
    tablestring = ('CREATE TABLE {tablename} '
        '(id serial PRIMARY KEY, '
        'name text UNIQUE);'
        .format(tablename=CURATORTABLE)
        )
    create_table(connection,cursor,CURATORTABLE,tablestring)

    # study-curator table
    CURATORSTUDYTABLE = config_dict['tables']['curatorstudytable']
    tablestring = ('CREATE TABLE {tablename} '
        '(curator_id int REFERENCES curator (id) ON DELETE CASCADE,'
        'study_id text REFERENCES study (id) ON DELETE CASCADE);'
        .format(tablename=CURATORSTUDYTABLE)
        )
    create_table(connection,cursor,CURATORSTUDYTABLE,tablestring)

    # otu table
    # OTUTABLE = config_dict['tables']['otutable']
    # tablestring = ('CREATE TABLE {tablename} '
    #     '(id int PRIMARY KEY, '
    #     'name text NOT NULL);'
    #     .format(tablename=OTUTABLE)
    #     )
    # create_table(connection,cursor,OTUTABLE,tablestring)

    # taxonomy table
    TAXONOMYTABLE = config_dict['tables']['otttable']
    tablestring = ('CREATE TABLE {tablename} '
        '(id int PRIMARY KEY, '
        'name text, '
        'parent int);'
        .format(tablename=TAXONOMYTABLE)
    )
    create_table(connection,cursor,TAXONOMYTABLE,tablestring)

    # otu-tree table
    TREEOTUTABLE = config_dict['tables']['treeotutable']
    tablestring = ('CREATE TABLE {tablename} '
        '(tree_id int REFERENCES tree (id) ON DELETE CASCADE, '
        'ott_id int REFERENCES taxonomy (id) ON DELETE CASCADE);'
        .format(tablename=TREEOTUTABLE)
        )
    create_table(connection,cursor,TREEOTUTABLE,tablestring)

    # synonym table
    SYNONYMTABLE = config_dict['tables']['synonymtable']
    tablestring = ('CREATE TABLE {tablename} '
        '(id int REFERENCES taxonomy (id) ON DELETE CASCADE, '
        'synonym text);'
        .format(tablename=SYNONYMTABLE)
    )
    create_table(connection,cursor,SYNONYMTABLE,tablestring)

def delete_table(connection,cursor,tablename):
    try:
        #print 'deleting table',tablename
        sqlstring=('DROP TABLE IF EXISTS '
            '{name} CASCADE;'
            .format(name=tablename)
            )
        cursor.execute(sqlstring)
        connection.commit()
    except psy.ProgrammingError, ex:
        print 'Error deleting table {name}'.format(name=tablename)

def delete_all_tables(connection,cursor,config_dict):
    print 'deleting tables'
    tabledict = config_dict['tables']
    for table in tabledict:
        name = tabledict[table]
        delete_table(connection,cursor,name)

def index_json_columns(connection,cursor,config_dict):
    #print "creating GIN index on JSONB columns in TREE and STUDY tables"
    try:
        # STUDY INDEX
        STUDYGININDEX=config_dict['studyginindex']
        STUDYTABLE = config_dict['tables']['studytable']
        sqlstring = ('CREATE INDEX {indexname} on {tablename} '
            'USING gin({column});'
            .format(indexname=STUDYGININDEX,tablename=STUDYTABLE,column='data'))
        cursor.execute(sqlstring)
        connection.commit()
        # TREE INDEX
        TREEGININDEX=config_dict['treeginindex']
        TREETABLE = config_dict['tables']['treetable']
        sqlstring = ('CREATE INDEX {indexname} on {tablename} '
            'USING gin({column});'
            .format(indexname=TREEGININDEX,tablename=TREETABLE,column='data'))
        cursor.execute(sqlstring)
        connection.commit()
    except psy.ProgrammingError, ex:
        print 'Error creating GIN index'

# imports csv data into the database using the (faster) bulk copy method
# used to load otu_tree_map table and taxonomy tables
def import_csv_file(connection,cursor,table,filename):
    print "copying {f} into {t} table".format(f=filename,t=table)
    with open (filename,'r') as f:
        copystring="COPY {t} FROM STDIN WITH CSV HEADER".format(t=table)
        cursor.copy_expert(copystring,f)
        connection.commit()

# Config file contains these variables
# connection_info:
#   dbname, user
# tables:
#   curatorstudytable, otutable, curatortable, treetable, studytable
# ginindex:
def read_config(configfile):
    with open(configfile,'r') as f:
        config_dict = yaml.safe_load(f)
        return config_dict

def table_exists(cursor, tablename):
    sqlstring = ("SELECT EXISTS (SELECT 1 "
        "FROM information_schema.tables "
        "WHERE table_schema = 'public' "
        "AND table_name = '{0}');"
        .format(tablename)
        )
    cursor.execute(sqlstring)
    return cursor.fetchone()[0]

# TODO: need to hook this in, probably through config file
# def get_logger(name='ottreeindex'):
#     logger = logging.getLogger(name)
#     logger.basicConfig(filename='setup_db.log',level=logging.INFO)

if __name__ == "__main__":
    # get command line argument (option to delete tables and start over)
    parser = argparse.ArgumentParser(description='set up database tables')
    parser.add_argument('configfile',
        help='path to the config file'
        )

    parser.add_argument('-d',
        dest='delete_tables',
        action='store_true',
        default=False,
        help='use this flag to delete tables at start'
        )

    args = parser.parse_args()

    config_dict = read_config(args.configfile)
    connection, cursor = connect(config_dict)

    if connection != None:
        try:
            if (args.delete_tables):
                delete_all_tables(connection,cursor,config_dict)
                create_all_tables(connection,cursor,config_dict)
            else:
                create_all_tables(connection,cursor,config_dict)
                clear_tables(connection,cursor,config_dict)
        except psy.Error as e:
            print e.pgerror

        connection.close()
