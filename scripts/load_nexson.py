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
CURATORSTUDYTABLE='curator_study_map'
GININDEX='study_ix_jsondata_gin'

def clear_tables(cursor):
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

# check if tables exist, and if not, create them
def create_tables(cursor):
    # create study table
    if (table_exists(cursor,STUDYTABLE)):
        print 'study table exists'
    else:
        tablestring = ('CREATE TABLE {tablename} '
            '(id text PRIMARY KEY, '
            'year integer, '
            'data jsonb);'
            .format(tablename=STUDYTABLE)
            )
        cursor.execute(tablestring)
    # tree table
    if (table_exists(cursor,TREETABLE)):
        print 'tree table exists'
    else:
        tablestring = ('CREATE TABLE {tablename} '
            '(id text NOT NULL, '
            'study_id text REFERENCES study (id), '
            'PRIMARY KEY (study_id,id));'
            .format(tablename=TREETABLE)
            )
        cursor.execute(tablestring)
    # TODO: curator table
    if (table_exists(cursor,CURATORTABLE)):
        print 'curator table exists'
    else:
        tablestring = ('CREATE TABLE {tablename} '
            '(id serial PRIMARY KEY, '
            'name text NOT NULL);'
            .format(tablename=CURATORTABLE)
            )
        cursor.execute(tablestring)
    # TODO: study-curator table
    if (table_exists(cursor,CURATORSTUDYTABLE)):
        print 'curator_study_map table exists'
    else:
        tablestring = ('CREATE TABLE {tablename} '
            '(curator_id int REFERENCES curator (id) ,'
            'study_id text REFERENCES study (id));'
            .format(tablename=CURATORSTUDYTABLE)
            )
        cursor.execute(tablestring)

def index_json_column(cursor):
    sqlstring = ('CREATE INDEX {indexname} on {tablename} '
        'USING gin({column});'
        .format(indexname=GININDEX,tablename=STUDYTABLE,column='data'))
    cursor.execute(sqlstring)

def create_phylesystem_obj():
    # create connection to local phylesystem
    phylesystem_api_wrapper = PhylesystemAPI(get_from='local')
    phylesystem = phylesystem_api_wrapper.phylesystem_obj
    return phylesystem

# iterate over phylesystem nexsons and import
# set nstudies if you want to limit to some number
# for testing rather than importing them all
def load_nexsons(connection,cursor,phy,nstudies=None):
    counter = 0
    for study_id, n in phy.iter_study_objs():
        print 'STUDY ',study_id
        # get data for INSERT statement for study
        # INSERT into study (studyid,year,data) VALUES ('studyid','year','data');
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

        # iterate over curators, adding curators to curator table and the
        # who-curated-what relationship to study-curator-map
        # note that ot:curators might be a string and might be a list
        c = nexml.get('^ot:curatorName')
        #print ' ot:curatorName: ',c
        curators=[]
        if (isinstance(c,basestring)):
            curators.append(c)
        else:
            curators=c

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

        # iterate over trees and insert into Tree table
        for trees_group_id, tree_id, tree in iter_trees(n):
            print ' tree :' ,tree_id
            # INSERT into tree (treeid,studyid) VALUES ('tree_id','study_id')
            sqlstring = ("INSERT INTO {tablename} (id,study_id)"
                "VALUES (%s,%s);"
                .format(tablename=TREETABLE)
                )
            data = (tree_id,study_id)
            cursor.execute(sqlstring,data)
        connection.commit()

        counter+=1
        if (nstudies and counter>=nstudies):
            print "inserted ",nstudies," studies"
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
    connection, cursor = connect()
    try:
        create_tables(cursor)
    except psy.Error as e:
        print e.pgerror
    starttime = dt.datetime.now()
    try:
        phy = create_phylesystem_obj()
        clear_tables(cursor)
        load_nexsons(connection,cursor,phy,15)
        index_json_column(cursor)
    except psy.Error as e:
        print e.pgerror
    #load_nexsons(connection,cursor)
    connection.close()
    endtime = dt.datetime.now()
    print "Load time: ",endtime - starttime
