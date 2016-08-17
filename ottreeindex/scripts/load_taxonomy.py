# Imports nexson files from the OpenTree API into a postgres database
#   uses the phylesystem API via the peyotl library
# Assumes database already set up. This happends either in initializedb.py
#   if running pyramid app or setup_db.py for testing (both in
#   this same directory)

import datetime as dt
import argparse
import psycopg2 as psy
# import simplejson as json
import yaml
# import re

# other database functions
import setup_db

# # peyotl setup
# from peyotl.api.phylesystem_api import PhylesystemAPI
# from peyotl.manip import iter_trees
# from peyotl import gen_otu_dict, iter_node
# from peyotl.phylesystem.phylesystem_umbrella import Phylesystem
# from peyotl.nexson_syntax import get_nexml_el

import peyotl.ott as ott

def load_taxonomy(connection,cursor,otttable,syntable,path):
    taxonomy = ott.OTT(ott_loc)
    # get dictionary of ottids:ottnames, noting that the names can be strings
    # or tuples, e.g. (canonical name,synonym,synonym)
    ott_names = taxonomy.ott_id_to_names

    # dictionary of ottid:parent_ottid
    ott_parents = taxonomy.ott_id2par_ott_id
    for ott_id in ott_names:
        name = ott_names[ott_id]
        synonyms=[]
        # if names is a tuple, then the first element is the unique name
        # and the others are synonyms
        if (isinstance(name,tuple)):
            synonyms = name[1:]
            name = name[0]
        parent_id = ott_parents[ott_id]

        # insert into taxonomy table
        sqlstring = ("INSERT INTO {t} "
            "(ott_id,ott_name,parent) "
            "VALUES (%s,%s,%s);"
            .format(t=otttable)
            )
        data = (ott_id,name,parent_id)
        #print '  SQL: ',cursor.mogrify(sqlstring,data)
        cursor.execute(sqlstring,data)

        # insert into synonym table
        for s in synonyms:
            sqlstring = ("INSERT INTO {t} "
                "(ott_id,synonym) "
                "VALUES (%s,%s);"
                .format(t=syntable)
                )
            data = (ott_id,s)
            #print '  SQL: ',cursor.mogrify(sqlstring,data)
            cursor.execute(sqlstring,data)

    connection.commit()

if __name__ == "__main__":
    # get command line argument (nstudies to import)
    parser = argparse.ArgumentParser(description='load ott into postgres')
    parser.add_argument('configfile',
        help='path to the config file'
        )
    args = parser.parse_args()

    # read config variables
    config_dict={}
    with open(args.configfile,'r') as f:
        config_dict = yaml.safe_load(f)

    connection, cursor = setup_db.connect(config_dict)

    # test that table exists
    # and clear data
    try:
        TAXONOMYTABLE = config_dict['tables']['otttable']
        SYNONYMTABLE = config_dict['tables']['synonymtable']
        if not setup_db.table_exists(cursor,TAXONOMYTABLE):
            raise psy.ProgrammingError("Table {t} does not exist".format(t=TAXONOMYTABLE))
        if not setup_db.table_exists(cursor,SYNONYMTABLE):
            raise psy.ProgrammingError("Table {t} does not exist".format(t=SYNONYMTABLE))
        setup_db.clear_single_table(connection,cursor,TAXONOMYTABLE)
        setup_db.clear_single_table(connection,cursor,SYNONYMTABLE)
        print "done clearing tables"
    except psy.Error as e:
        print e.pgerror

    try:
        ott_loc = config_dict['taxonomy']
        if ott_loc == 'None':
            print 'No taxonomy'
        else:
            # data import
            starttime = dt.datetime.now()
            load_taxonomy(connection,cursor,TAXONOMYTABLE,SYNONYMTABLE,ott_loc)
            print "Loading taxonomy"
            endtime = dt.datetime.now()
            print "OTT load time: ",endtime - starttime
    except psy.Error as e:
        print e.pgerror
    connection.close()
