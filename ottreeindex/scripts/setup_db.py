# Sets up the postgres database for future nexson import
# Deletes existing tables and re-creates them
# Also includes some utility functions

import argparse
import yaml
import psycopg2 as psy
import simplejson as json
from collections import defaultdict
import pdb

def clear_gin_index(connection,cursor,config_dict):
    GININDEX=config_dict['ginindex']
    sqlstring = "DROP INDEX IF EXISTS {indexname};".format(indexname=GININDEX)
    cursor.execute(sqlstring)
    connection.commit()

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
        print e.pgerror
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

# check if tables exist, and if not, create them
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
        'tree_label text NOT NULL, '
        'study_id text REFERENCES study (id), '
        'UNIQUE (tree_label,study_id));'
        .format(tablename=TREETABLE)
        )
    create_table(connection,cursor,TREETABLE,tablestring)

    # curator table
    CURATORTABLE = config_dict['tables']['curatortable']
    tablestring = ('CREATE TABLE {tablename} '
        '(id serial PRIMARY KEY, '
        'name text NOT NULL);'
        .format(tablename=CURATORTABLE)
        )
    create_table(connection,cursor,CURATORTABLE,tablestring)

    # study-curator table
    CURATORSTUDYTABLE = config_dict['tables']['curatorstudytable']
    tablestring = ('CREATE TABLE {tablename} '
        '(curator_id int REFERENCES curator (id) ,'
        'study_id text REFERENCES study (id));'
        .format(tablename=CURATORSTUDYTABLE)
        )
    create_table(connection,cursor,CURATORSTUDYTABLE,tablestring)

    # OTU-tree table
    OTUTABLE = config_dict['tables']['otutable']
    tablestring = ('CREATE TABLE {tablename} '
        '(id int PRIMARY KEY, '
        'ott_name text, '
        'tree_id int REFERENCES tree (id));'
        .format(tablename=OTUTABLE)
        )
    create_table(connection,cursor,OTUTABLE,tablestring)

def delete_table(connection,cursor,tablename):
    try:
        print 'deleting table',tablename
        sqlstring=('DROP TABLE IF EXISTS '
            '{name} CASCADE;'
            .format(name=tablename)
            )
        cursor.execute(sqlstring)
        connection.commit()
    except psy.ProgrammingError, ex:
        print 'Error deleting table {name}'.format(name=tablename)

def delete_all_tables(connection,cursor,config_dict):
    tabledict = config_dict['tables']
    for table in tabledict:
        name = tabledict[table]
        delete_table(connection,cursor,name)

def index_json_column(connection,cursor,config_dict):
    print "creating GIN index on JSON column"
    try:
        GININDEX = config_dict['ginindex']
        sqlstring = ('CREATE INDEX {indexname} on {tablename} '
            'USING gin({column});'
            .format(indexname=GININDEX,tablename=STUDYTABLE,column='data'))
        cursor.execute(sqlstring)
        connection.commit()
    except psy.ProgrammingError, ex:
        print 'Error creating GIN index'

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

if __name__ == "__main__":
    # get command line argument (option to delete tables and start over)
    parser = argparse.ArgumentParser(description='set up database tables')
    parser.add_argument('configfile',
        help='path to the config file'
        )
    args = parser.parse_args()

    config_dict = read_config(args.configfile)
    connection, cursor = connect(config_dict)

    #pdb.set_trace()
    try:
        delete_all_tables(connection,cursor,config_dict)
        create_all_tables(connection,cursor,config_dict)
    except psy.Error as e:
        print e.pgerror

    connection.close()
