# Imports nexson files from the OpenTree API into a postgres database
#   uses the phylesystem API via the peyotl library
# Assumes database already set up. This happends either in initializedb.py
#   if running pyramid app or setup_db.py for testing (both in
#   this same directory)

import datetime as dt
import argparse
import psycopg2 as psy
import simplejson as json
import yaml

# other database functions
import setup_db

# peyotl setup
from peyotl.api.phylesystem_api import PhylesystemAPI
from peyotl.manip import iter_trees
from peyotl import gen_otu_dict, iter_node
from peyotl.phylesystem.phylesystem_umbrella import Phylesystem
from peyotl.nexson_syntax import get_nexml_el

def clear_gin_index(connection,cursor,GININDEX):
    # also remove the index
    sqlstring = "DROP INDEX IF EXISTS {indexname};".format(indexname=GININDEX)
    cursor.execute(sqlstring)
    connection.commit()

# create the JSON GIN index
def index_json_column(connection,cursor):
    print "creating GIN index on JSON column"
    try:
        sqlstring = ('CREATE INDEX {indexname} on {tablename} '
            'USING gin({column});'
            .format(indexname=GININDEX,tablename=STUDYTABLE,column='data'))
        cursor.execute(sqlstring)
        connection.commit()
    except psy.Error as e:
        print 'Error creating GIN index'
        print e.pgerror

# iterate over curators, adding curators to curator table and the
# who-curated-what relationship to study-curator-map
def insert_curators(connection,cursor,study_id,curators):
    try:
        for name in curators:
            sqlstring = ('INSERT INTO {tablename} (name) '
                'VALUES (%s);'
                .format(tablename=CURATORTABLE)
                )
            data = (name)
            print '  SQL: ',cursor.mogrify(sqlstring,(data,))
            cursor.execute(sqlstring,(data,))

            # need to get curator id for insertion into map table
            sqlstring = ('SELECT id FROM {tablename} '
                'WHERE name=%s;'
                .format(tablename=CURATORTABLE)
                )
            data=(name)
            print '  SQL: ',cursor.mogrify(sqlstring,(data,))
            cursor.execute(sqlstring,(data,))
            curator_id = cursor.fetchone()
            sqlstring = ('INSERT INTO {tablename} (curator_id,study_id) '
                'VALUES (%s,%s);'
                .format(tablename=CURATORSTUDYTABLE)
                )
            data = (curator_id,study_id)
            print '  SQL: ',cursor.mogrify(sqlstring,data)
            cursor.execute(sqlstring,data)
            connection.commit()
    except psy.ProgrammingError, ex:
        print 'Error inserting curator'

# iterate over phylesystem nexsons and import
def load_nexsons(connection,cursor,phy,nstudies=None):
    counter = 0
    for study_id, studyobj in phy.iter_study_objs():
        print 'STUDY: ',study_id

        # study data for study table
        nexml = get_nexml_el(studyobj)
        year = nexml.get('^ot:studyYear')
        jsonstring = json.dumps(nexml)
        sqlstring = ("INSERT INTO {tablename} (id, year, data) "
            "VALUES (%s,%s,%s);"
            .format(tablename=STUDYTABLE)
            )
        data = (study_id,year,jsonstring)
        #print '  SQL: ',cursor.mogrify(sqlstring,data)
        cursor.execute(sqlstring,data)
        connection.commit()

        # get curator(s), noting that ot:curators might be a
        # string or a list
        print " inserting curator data"
        c = nexml.get('^ot:curatorName')
        print ' ot:curatorName: ',c
        curators=[]
        if (isinstance(c,basestring)):
            curators.append(c)
        else:
            curators=c
        insert_curators(connection,cursor,study_id,curators)

        # iterate over trees and insert tree data
        # note that OTU data done separately as COPY
        # due to size of table (see script <scriptname>)
        print ' inserting tree data'
        try:
            for trees_group_id, tree_id, tree in iter_trees(studyobj):
                print ' tree :' ,tree_id
                sqlstring = ("INSERT INTO {tablename} (tree_id,study_id)"
                    "VALUES (%s,%s);"
                    .format(tablename=TREETABLE)
                    )
                data = (tree_id,study_id)
                print '  SQL: ',cursor.mogrify(sqlstring,data)
                cursor.execute(sqlstring,data)
                connection.commit()
        except psy.ProgrammingError, ex:
            print 'Error inserting curator'

        counter+=1
        if (nstudies and counter>=nstudies):
            print "inserted",nstudies,"studies"
            break

if __name__ == "__main__":
    # get command line argument (nstudies to import)
    parser = argparse.ArgumentParser(description='load nexsons into postgres')
    parser.add_argument('configfile',
        help='path to the config file'
        )
    parser.add_argument('-n',
        dest='nstudies',
        type=int,
        help='load only n studies; if absent, load all studies'
        )
    args = parser.parse_args()

    # read config variables
    config_dict={}
    with open(args.configfile,'r') as f:
        config_dict = yaml.safe_load(f)

    connection, cursor = setup_db.connect(config_dict)

    # test that tables exist
    tabledict = config_dict['tables']
    for table in tabledict:
        name = tabledict[table]
        if not setup_db.table_exists(cursor,name):
            raise psy.ProgrammingError("Table {t} does not exist".format(t=name))
    clear_gin_index(connection,cursor)

    # data import
    starttime = dt.datetime.now()
    try:
        # TODO: catch peyotl-specific exceptions
        phy = setup_db.create_phylesystem_obj()
        if (args.nstudies):
            load_nexsons(connection,cursor,phy,args.nstudies)
        else:
            load_nexsons(connection,cursor)
        index_json_column(connection,cursor,phy)
    except psy.Error as e:
        print e.pgerror
    connection.close()
    endtime = dt.datetime.now()
    print "Load time: ",endtime - starttime
