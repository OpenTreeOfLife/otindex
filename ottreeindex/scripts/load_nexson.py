# Imports nexson files from the OpenTree API into a postgres database
# uses the phylesystem API via the peyotl library

import datetime as dt
import argparse
import psycopg2 as psy
import simplejson as json
from collections import defaultdict

# peyotl setup
from peyotl.api.phylesystem_api import PhylesystemAPI
from peyotl.manip import iter_trees
from peyotl.phylesystem.phylesystem_umbrella import Phylesystem
from peyotl.nexson_syntax import get_nexml_el

# fill these in as they are for your system
DBNAME = 'newoti'
USER = 'pguser'
STUDYTABLE = 'study'
TREETABLE = 'tree'
CURATORTABLE='curator'
OTUTABLE='otu'
CURATORSTUDYTABLE='curator_study_map'
GININDEX='study_ix_jsondata_gin'
tablelist = [STUDYTABLE,TREETABLE,CURATORTABLE,OTUTABLE,CURATORSTUDYTABLE]

def clear_tables(cursor):
    print 'clearing tables'
    # tree linked to study via foreign key, so cascade removes both
    cursor.execute('TRUNCATE study CASCADE;')
    cursor.execute('TRUNCATE curator CASCADE;')

    # also remove the index (so that re-loading is faster)
    sqlstring = "DROP INDEX IF EXISTS {indexname};".format(indexname=GININDEX)
    cursor.execute(sqlstring)

def connect():
    try:
        connectionstring="dbname={dbname} user={dbuser}".format(dbname=DBNAME,dbuser=USER)
        conn = psy.connect(connectionstring)
        cursor = conn.cursor()
    except KeyboardInterrupt:
        print "Shutdown requested because could not connect to DB"
    except Exception:
        traceback.print_exc(file=sys.stdout)
    return (conn,cursor)

def create_phylesystem_obj():
    # create connection to local phylesystem
    phylesystem_api_wrapper = PhylesystemAPI(get_from='local')
    phylesystem = phylesystem_api_wrapper.phylesystem_obj
    return phylesystem

def create_single_table(cursor,tablename,tablestring):
    print 'creating table',tablename
    if (table_exists(cursor,tablename)):
        print '{table} exists'.format(table=tablename)
    else:
        cursor.execute(tablestring)

# check if tables exist, and if not, create them
def create_all_tables(cursor):
    # study table
    tablestring = ('CREATE TABLE {tablename} '
        '(id text PRIMARY KEY, '
        'year integer, '
        'data jsonb);'
        .format(tablename=STUDYTABLE)
        )
    create_single_table(cursor,STUDYTABLE,tablestring)

    # tree table
    tablestring = ('CREATE TABLE {tablename} '
        '(id serial PRIMARY KEY, '
        'tree_id text NOT NULL, '
        'study_id text REFERENCES study (id), '
        'UNIQUE (tree_id,study_id));'
        .format(tablename=TREETABLE)
        )
    create_single_table(cursor,TREETABLE,tablestring)

    # curator table
    tablestring = ('CREATE TABLE {tablename} '
        '(id serial PRIMARY KEY, '
        'name text NOT NULL);'
        .format(tablename=CURATORTABLE)
        )
    create_single_table(cursor,CURATORTABLE,tablestring)

    # study-curator table
    tablestring = ('CREATE TABLE {tablename} '
        '(curator_id int REFERENCES curator (id) ,'
        'study_id text REFERENCES study (id));'
        .format(tablename=CURATORSTUDYTABLE)
        )
    create_single_table(cursor,CURATORSTUDYTABLE,tablestring)

    # OTU-tree table
    tablestring = ('CREATE TABLE {tablename} '
        '(id int PRIMARY KEY, '
        'ott_name text, '
        'tree_id int REFERENCES tree (id));'
        .format(tablename=OTUTABLE)
        )
    create_single_table(cursor,OTUTABLE,tablestring)

def delete_tables(cursor):
    print 'deleting tables'
    for table in tablelist:
        sqlstring=('DROP TABLE IF EXISTS '
            '{name} CASCADE;'
            .format(name=table)
            )
        cursor.execute(sqlstring)

def index_json_column(cursor):
    sqlstring = ('CREATE INDEX {indexname} on {tablename} '
        'USING gin({column});'
        .format(indexname=GININDEX,tablename=STUDYTABLE,column='data'))
    cursor.execute(sqlstring)

# iterate over phylesystem nexsons and import
def load_nexsons(connection,cursor,phy,nstudies=None):
    counter = 0
    for study_id, n in phy.iter_study_objs():
        print 'STUDY ',study_id
        # get data for INSERT statement for study
        nexml = get_nexml_el(n)
        year = nexml.get('^ot:studyYear')
        jsonstring = json.dumps(nexml)
        sqlstring = ("INSERT INTO {tablename} (id, year, data) "
            "VALUES (%s,%s,%s);"
            .format(tablename=STUDYTABLE)
            )
        data = (study_id,year,jsonstring)
        #print sqlstring
        cursor.execute(sqlstring,data)
        connection.commit()

        # get curator(s), noting that ot:curators might be a string
        # or a list
        c = nexml.get('^ot:curatorName')
        #print ' ot:curatorName: ',c
        curators=[]
        if (isinstance(c,basestring)):
            curators.append(c)
        else:
            curators=c

        # iterate over curators, adding curators to curator table and the
        # who-curated-what relationship to study-curator-map
        for name in curators:
            sqlstring = ('INSERT INTO {tablename} (name) '
                'VALUES (%s);'
                .format(tablename=CURATORTABLE)
                )
            data = (name)
            #print '  SQL: ',cursor.mogrify(sqlstring,(data,))
            cursor.execute(sqlstring,(data,))

            # need to get curator id for insertion into map table
            sqlstring = ('SELECT id FROM {tablename} '
                'WHERE name=%s;'
                .format(tablename=CURATORTABLE)
                )
            data=(name)
            #print '  SQL: ',cursor.mogrify(sqlstring,(data,))
            cursor.execute(sqlstring,(data,))
            curator_id = cursor.fetchone()
            sqlstring = ('INSERT INTO {tablename} (curator_id,study_id) '
                'VALUES (%s,%s);'
                .format(tablename=CURATORSTUDYTABLE)
                )
            data = (curator_id,study_id)
            print '  SQL: ',cursor.mogrify(sqlstring,data)
            cursor.execute(sqlstring,data)

        # iterate over trees and insert into tree table
        for trees_group_id, tree_id, tree in iter_trees(n):
            print ' tree :' ,tree_id
            sqlstring = ("INSERT INTO {tablename} (tree_id,study_id)"
                "VALUES (%s,%s);"
                .format(tablename=TREETABLE)
                )
            data = (tree_id,study_id)
            cursor.execute(sqlstring,data)
        connection.commit()

        counter+=1
        if (nstudies and counter>=nstudies):
            print "inserted",nstudies,"studies"
            break

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
    # get command line argument (nstudies to import)
    parser = argparse.ArgumentParser(description='load nexsons into postgres')
    parser.add_argument('-d',
        dest='delete_tables',
        action='store_true',
        default=False,
        help='use this flag to delete tables at start'
        )
    parser.add_argument('-n',
        dest='nstudies',
        type=int,
        help='load only n studies; if absent, load all studies'
        )
    args = parser.parse_args()
    connection, cursor = connect()

    # optionally delete and then create the
    # tables, if they do not already exist
    try:
        if (args.delete_tables):
            delete_tables(cursor)
            create_all_tables(cursor)
        else:
            create_all_tables(cursor)
            clear_tables(cursor)
    except psy.Error as e:
        print e.pgerror

    # data import
    starttime = dt.datetime.now()
    try:
        # TODO: catch peyotl-specific exceptions
        phy = create_phylesystem_obj()
        if (args.nstudies):
            load_nexsons(connection,cursor,phy,args.nstudies)
        else:
            load_nexsons(connection,cursor)
        index_json_column(cursor)
    except psy.Error as e:
        print e.pgerror
    except Exception:
        print "unspecified error"
    connection.close()
    endtime = dt.datetime.now()
    print "Load time: ",endtime - starttime
