# Imports nexson files from the OpenTree API into a postgres database
# uses the phylesystem API via the peyotl library

import sys,traceback
import datetime as dt
import argparse
import glob
import psycopg2 as psy
import simplejson as json
from collections import defaultdict

# peyotl setup
from peyotl.api.phylesystem_api import PhylesystemAPI
from peyotl.manip import iter_trees
from peyotl.phylesystem.phylesystem_umbrella import Phylesystem
from peyotl.nexson_syntax import get_nexml_el

# fill these in as they are for your system
STUDYTABLE = 'study'
TREETABLE = 'tree'
DBNAME = 'newoti'
USER = 'pguser'

# check if tables exist, and if not, create them
def create_tables(cursor):
    # study table
    if (table_exists(cursor,STUDYTABLE)):
        print 'study table exists'
    else:
        tablestring = ('CREATE TABLE {tablename} '
            '(studyid text PRIMARY KEY, '
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
            '(treeid text NOT NULL, '
            'studyid text REFERENCES study (studyid), '
            'PRIMARY KEY (studyid,treeid));'
            .format(tablename=TREETABLE)
            )
        cursor.execute(tablestring)
    # TODO: curator table
    # TODO: study-curator table

def table_exists(cursor, tablename):
    sqlstring = ("SELECT EXISTS (SELECT 1 "
        "FROM information_schema.tables "
        "WHERE table_schema = 'public' "
        "AND table_name = '{0}');"
        .format(tablename)
        )
    cursor.execute(sqlstring)
    return cursor.fetchone()[0]

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

def clear_tables(cursor):
    print "truncating tables tree and study"
    cursor.execute('TRUNCATE study CASCADE;')
    #cursor.execute('TRUNCATE study;')

# iterate over phylesystem nexsons and import
# set nstudies if you want to limit to some number
# rather than importing them all
def load_nexsons(connection,cursor,nstudies=None):
    # create connection to local phylesystem
    phylesystem_api_wrapper = PhylesystemAPI(get_from='local')
    phy = phylesystem_api_wrapper.phylesystem_obj
    counter = 0
    for study_id, n in phy.iter_study_objs():
        # get data for INSERT statement for study
        # INSERT into study (studyid,year,data) VALUES ('studyid','year','data');
        nexml = get_nexml_el(n)
        year = nexml.get('^ot:studyYear')
        jsonstring = json.dumps(nexml)
        sqlstring = ("INSERT INTO study (studyid, year, data) "
            "VALUES (%s,%s,%s)")
        data = (study_id,year,jsonstring)
        #print sqlstring
        cursor.execute(sqlstring,data)
        connection.commit()

        # iterate over trees and insert into Tree table
        for trees_group_id, tree_id, tree in iter_trees(n):
            print study_id,' : ', tree_id
            # INSERT into tree (treeid,studyid) VALUES ('tree_id','study_id')
            sqlstring = ("INSERT INTO tree (treeid,studyid)"
                "VALUES (%s,%s)")
            data = (tree_id,study_id)
            cursor.execute(sqlstring,data)
        connection.commit()

        counter+=1
        if (nstudies and counter>=nstudies):
            print "inserted ",nstudies," studies"
            break

        #with open(filename) as data_file:
            # round trip using simpljson for safety
            #data = json.load(data_file)
            #jsonstring = json.dumps(data)
            # QuotedString escapes single quotes, line breaks, etc
            #qline = psy.extensions.QuotedString(jsonstring).getquoted()
            #SQL="INSERT INTO %(table)s (%(column)s) VALUES (%(data)s)" % {"table":TABLE, "column":COLUMN, "data":qline}
            #cursor.execute(SQL)
            #connection.commit()

if __name__ == "__main__":
    connection, cursor = connect()
    try:
        create_tables(cursor)
    except psy.Error as e:
        print e.pgerror
    starttime = dt.datetime.now()
    print starttime
    try:
        clear_tables(cursor)
        load_nexsons(connection,cursor,nstudies=3)
    except psy.Error as e:
        print e.pgerror
    #load_nexsons(connection,cursor)
    connection.close()
    endtime = dt.datetime.now()
    print "Elapsed: ",endtime - starttime
