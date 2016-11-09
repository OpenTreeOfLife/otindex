# Sets up the postgres database for future nexson import
# Deletes existing tables and re-creates them
# Also includes some utility functions

# Changes to table structure must be replicated in ../models.py

import argparse
import ConfigParser
import psycopg2 as psy
import simplejson as json
import pdb

def clear_gin_index(connection,cursor):
    print 'clearing GIN indexes'
    # study table
    sqlstring = "DROP INDEX IF EXISTS study_ix_jsondata_gin;"
    cursor.execute(sqlstring)
    # tree table
    sqlstring = "DROP INDEX IF EXISTS tree_ix_jsondata_gin;"
    cursor.execute(sqlstring)

    connection.commit()

def clear_single_table(connection,cursor,tablename):
    print 'clearing table',tablename
    sqlstring=('TRUNCATE {t} CASCADE;').format(t=tablename)
    cursor.execute(sqlstring)

def clear_tables(connection,cursor,config_obj):
    print 'clearing tables'
    # tree linked to study via foreign key, so cascade removes both
    tabledict = dict(config_obj.items('database_tables'))
    for table in tabledict:
        name = tabledict[table]
        sqlstring=('TRUNCATE {t} CASCADE;'
            .format(t=name)
        )
        #print '  SQL: ',cursor.mogrify(sqlstring)
        cursor.execute(sqlstring)

def connect(config_obj):
    conn = cursor = None  # not sure of exception intent
    try:
        DBNAME = config_obj.get('connection_info','dbname')
        USER = config_obj.get('connection_info','dbuser')
        HOST = 'localhost'
        connectionstring = ""
        PASSWORD = config_obj.get('connection_info','password')
        # if there is no password specified
        if PASSWORD == '':
            connectionstring=("dbname={dbname} "
                "host={h} "
                "user={dbuser}"
                .format(dbname=DBNAME,h=HOST,dbuser=USER)
                )
        else:
            connectionstring=("dbname={dbname} "
                "user={dbuser} "
                "host={h} "
                "password={pwd}"
                .format(dbname=DBNAME,h=HOST,dbuser=USER,pwd=PASSWORD)
                )
        conn = psy.connect(connectionstring)
        cursor = conn.cursor()
    except ConfigParser.NoSectionError as e:
        print "Error reading config file; {m}".format(m=e.Error)
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
# otindex/models.py
def create_all_tables(connection,cursor,config_obj):
    # study table
    STUDYTABLE = config_obj.get('database_tables','studytable')
    tablestring = ('CREATE TABLE {tablename} '
        '(id text PRIMARY KEY, '
        'ntrees integer, '
        'treebase_id text, '
        'data jsonb);'
        .format(tablename=STUDYTABLE)
        )
    create_table(connection,cursor,STUDYTABLE,tablestring)

    # tree table
    TREETABLE = config_obj.get('database_tables','treetable')
    tablestring = ('CREATE TABLE {tablename} '
        '(id serial PRIMARY KEY, '
        'tree_id text NOT NULL, '
        'study_id text REFERENCES study (id) ON DELETE CASCADE, '
        'ntips Integer, '
        'proposed boolean, '
        'data jsonb, '
        'UNIQUE (tree_id,study_id));'
        .format(tablename=TREETABLE)
        )
    create_table(connection,cursor,TREETABLE,tablestring)

    # curator table
    CURATORTABLE = config_obj.get('database_tables','curatortable')
    tablestring = ('CREATE TABLE {tablename} '
        '(id serial PRIMARY KEY, '
        'name text UNIQUE);'
        .format(tablename=CURATORTABLE)
        )
    create_table(connection,cursor,CURATORTABLE,tablestring)

    # study-curator table
    CURATORSTUDYTABLE = config_obj.get('database_tables','curatorstudytable')
    tablestring = ('CREATE TABLE {tablename} '
        '(curator_id int REFERENCES curator (id) ON DELETE CASCADE,'
        'study_id text REFERENCES study (id) ON DELETE CASCADE);'
        .format(tablename=CURATORSTUDYTABLE)
        )
    create_table(connection,cursor,CURATORSTUDYTABLE,tablestring)

    # taxonomy table
    TAXONOMYTABLE = config_obj.get('database_tables','otttable')
    tablestring = ('CREATE TABLE {tablename} '
        '(id int PRIMARY KEY, '
        'name text, '
        'parent int);'
        .format(tablename=TAXONOMYTABLE)
    )
    create_table(connection,cursor,TAXONOMYTABLE,tablestring)

    # otu-tree table
    TREEOTUTABLE = config_obj.get('database_tables','treeotutable')
    tablestring = ('CREATE TABLE {tablename} '
        '(tree_id int REFERENCES tree (id) ON DELETE CASCADE, '
        'ott_id int REFERENCES taxonomy (id) ON DELETE CASCADE);'
        .format(tablename=TREEOTUTABLE)
        )
    create_table(connection,cursor,TREEOTUTABLE,tablestring)

    # synonym table
    SYNONYMTABLE = config_obj.get('database_tables','synonymtable')
    tablestring = ('CREATE TABLE {tablename} '
        '(id serial PRIMARY KEY, '
        'ott_id int REFERENCES taxonomy (id) ON DELETE CASCADE, '
        'synonym text);'
        .format(tablename=SYNONYMTABLE)
    )
    create_table(connection,cursor,SYNONYMTABLE,tablestring)

    # property table
    PROPERTYTABLE = config_obj.get('database_tables','propertytable')
    tablestring = ('CREATE TABLE {tablename} '
        '(id serial PRIMARY KEY, '
        'property text, '
        'prefix text, '
        'type text, '
        'UNIQUE (property,type));'
        .format(tablename=PROPERTYTABLE)
    )
    create_table(connection,cursor,PROPERTYTABLE,tablestring)

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

def delete_all_tables(connection,cursor,config_obj):
    print 'deleting tables'
    tabledict = dict(config_obj.items('database_tables'))
    for table in tabledict:
        name = tabledict[table]
        delete_table(connection,cursor,name)

def index_json_columns(connection,cursor,config_obj):
    #print "creating GIN index on JSONB columns in TREE and STUDY tables"
    try:
        # STUDY INDEX
        STUDYTABLE = config_obj.get('database_tables','studytable')
        sqlstring = ('CREATE INDEX study_ix_jsondata_gin on {tablename} '
            'USING gin({column});'
            .format(tablename=STUDYTABLE,column='data'))
        cursor.execute(sqlstring)
        connection.commit()
        # TREE INDEX
        TREETABLE = config_obj.get('database_tables','treetable')
        sqlstring = ('CREATE INDEX tree_ix_jsondata_gin on {tablename} '
            'USING gin({column});'
            .format(tablename=TREETABLE,column='data'))
        cursor.execute(sqlstring)
        connection.commit()
    except psy.ProgrammingError, ex:
        print 'Error creating GIN index'

# imports csv data into the database using the (faster) bulk copy method
# used to load otu_tree_map table and taxonomy tables
def import_csv_file(connection,cursor,table,filename):
    print "copying {f} into {t} table".format(f=filename,t=table)
    with open (filename,'r') as f:
        copystring="COPY {t}  FROM STDIN WITH CSV HEADER".format(t=table)
        cursor.copy_expert(copystring,f)
        connection.commit()

# Config file contains these sections
#  connection_info
#  tables
def read_config(configfile):
    config_obj = ConfigParser.SafeConfigParser()
    config_obj.read(configfile)
    return config_obj

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
        help='path to the development.ini file'
        )

    parser.add_argument('-d',
        dest='delete_tables',
        action='store_true',
        default=False,
        help='delete and re-create tables at start; default is to only clear tables'
        )

    args = parser.parse_args()

    config_obj = read_config(args.configfile)
    connection, cursor = connect(config_obj)

    if connection != None:
        try:
            if (args.delete_tables):
                delete_all_tables(connection,cursor,config_obj)
                create_all_tables(connection,cursor,config_obj)
            else:
                clear_tables(connection,cursor,config_obj)
        except psy.Error as e:
            print e.pgerror

        connection.close()
