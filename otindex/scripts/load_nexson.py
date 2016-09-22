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
import re

# other database functions
import setup_db

# peyotl setup
from peyotl.api.phylesystem_api import PhylesystemAPI
from peyotl.manip import iter_trees
from peyotl import gen_otu_dict, iter_node
from peyotl.phylesystem.phylesystem_umbrella import Phylesystem
from peyotl.nexson_syntax import get_nexml_el

def create_phylesystem_obj():
    # create connection to local phylesystem
    phylesystem_api_wrapper = PhylesystemAPI(get_from='local')
    phylesystem = phylesystem_api_wrapper.phylesystem_obj
    return phylesystem

# create the JSON GIN indexes
# def index_json_columns(connection,cursor,config_dict):
#     try:
#         # STUDY INDEX
#         STUDYGININDEX=config_dict['studyginindex']
#         STUDYTABLE = config_dict['tables']['studytable']
#         sqlstring = ('CREATE INDEX {indexname} on {tablename} '
#             'USING gin({column});'
#             .format(indexname=STUDYGININDEX,tablename=STUDYTABLE,column='data'))
#         cursor.execute(sqlstring)
#         connection.commit()
#         # TREE INDEX
#         TREEGININDEX=config_dict['treeginindex']
#         TREETABLE = config_dict['tables']['treetable']
#         sqlstring = ('CREATE INDEX {indexname} on {tablename} '
#             'USING gin({column});'
#             .format(indexname=TREEGININDEX,tablename=TREETABLE,column='data'))
#         cursor.execute(sqlstring)
#         connection.commit()
#     except psy.Error as e:
#         print 'Error creating GIN index'
#         print e.pgerror

# iterate over curators, adding curators to curator table and the
# who-curated-what relationship to study-curator-map
def insert_curators(connection,cursor,config_dict,study_id,curators):
    try:
        CURATORTABLE = config_dict['tables']['curatortable']
        CURATORSTUDYTABLE = config_dict['tables']['curatorstudytable']
        for name in curators:
            # check to make sure this curator name doesn't exist already
            sqlstring = ('SELECT id FROM {tablename} '
                'WHERE name=%s;'
                .format(tablename=CURATORTABLE)
                )
            data=(name)
            cursor.execute(sqlstring,(data,))
            curator_id = cursor.fetchone()
            if curator_id is None:
                # insert the curator, returning the serial id, which
                # we will need shortly
                sqlstring = ('INSERT INTO {tablename} (name) '
                    'VALUES (%s) RETURNING id;'
                    .format(tablename=CURATORTABLE)
                    )
                data = (name)
                #print '  SQL: ',cursor.mogrify(sqlstring,(data,))
                cursor.execute(sqlstring,(data,))
                curator_id = cursor.fetchone()

            # now insert the curator - study mapping
            sqlstring = ('INSERT INTO {tablename} (curator_id,study_id) '
                'VALUES (%s,%s);'
                .format(tablename=CURATORSTUDYTABLE)
                )
            data = (curator_id,study_id)
            #print '  SQL: ',cursor.mogrify(sqlstring,data)
            cursor.execute(sqlstring,data)
        connection.commit()
    except psy.ProgrammingError, ex:
        print 'Error inserting curator'

# load the nexson properties into a table
def load_properties(connection,cursor,prop_table,study_props,tree_props):
    for p in study_props:
        # remove the '^' or '@' at the start of the property
        # should be true for all properties, but check just in case
        if p.startswith('^') || p.startswith('@'):
            p = p[1:]
        sqlstring = ("INSERT INTO {t} (property,type) "
            "VALUES (%s,%s);"
            .format(t=prop_table)
        )
        data = (p,'study')
        #print '  SQL: ',cursor.mogrify(sqlstring)
        cursor.execute(sqlstring,data)
        connection.commit()

    for p in tree_props:
        if p.startswith('^') || p.startswith('@'):
            p = p[1:]
        sqlstring = ("INSERT INTO {t} (property,type) "
            "VALUES (%s,%s);"
            .format(t=prop_table)
        )
        data = (p,'tree')
        #print '  SQL: ',cursor.mogrify(sqlstring)
        cursor.execute(sqlstring,data)
        connection.commit()

# iterate over phylesystem nexsons and import
def load_nexsons(connection,cursor,phy,config_dict,nstudies=None):
    counter = 0
    study_properties = set()
    tree_properties = set()
    for study_id, studyobj in phy.iter_study_objs():
        nexml = get_nexml_el(studyobj)
        #print 'STUDY: ',study_id
        study_properties.update(nexml.keys())
        # study data for study table
        STUDYTABLE = config_dict['tables']['studytable']
        year = nexml.get('^ot:studyYear')
        proposedTrees = nexml.get('^ot:candidateTreeForSynthesis')
        if proposedTrees is None:
            proposedTrees = []

        sqlstring = ("INSERT INTO {tablename} (id, year) "
            "VALUES (%s,%s);"
            .format(tablename=STUDYTABLE)
            )
        data = (study_id,year)
        #print '  SQL: ',cursor.mogrify(sqlstring)
        cursor.execute(sqlstring,data)
        connection.commit()

        # get curator(s), noting that ot:curators might be a
        # string or a list
        c = nexml.get('^ot:curatorName')
        #print ' ot:curatorName: ',c
        curators=[]
        if (isinstance(c,basestring)):
            curators.append(c)
        else:
            curators=c
        insert_curators(connection,cursor,config_dict,study_id,curators)

        # iterate over trees and insert tree data
        # note that OTU data done separately as COPY
        # due to size of table (see script <scriptname>)
        TREETABLE = config_dict['tables']['treetable']
        try:
            for trees_group_id, tree_id, tree in iter_trees(studyobj):
                #print ' tree :' ,tree_id
                proposedForSynth = False
                tree_properties.update(tree.keys())
                if (tree_id in proposedTrees):
                    proposedForSynth = True
                treejson = json.dumps(tree)
                ntips = 0
                for node_id, node in iter_node(tree):
                    oid = node.get('@otu')
                    # no @otu property on internal nodes
                    if oid is not None:
                        ntips+=1

                sqlstring = ("INSERT INTO {tablename} "
                    "(tree_id,study_id,ntips,proposed,data) "
                    "VALUES (%s,%s,%s,%s,%s);"
                    .format(tablename=TREETABLE)
                    )
                data = (tree_id,study_id,ntips,proposedForSynth,treejson)
                #print '  SQL: ',cursor.mogrify(sqlstring,data)
                cursor.execute(sqlstring,data)
                #connection.commit()
                # update with treebase id, if exists
                datadeposit = nexml.get('^ot:dataDeposit')
                if (datadeposit):
                    url = datadeposit['@href']
                    pattern = re.compile(u'.+TB2:(.+)$')
                    matchobj = re.match(pattern,url)
                    if (matchobj):
                        tb_id = matchobj.group(1)
                        sqlstring = ("UPDATE {tablename} "
                            "SET treebase_id=%s "
                            "WHERE tree_id = %s and study_id=%s;"
                            .format(tablename=TREETABLE)
                            )
                        data = (tb_id,tree_id,study_id)
                        #print '  SQL: ',cursor.mogrify(sqlstring,data)
                        cursor.execute(sqlstring,data)
                connection.commit()

        except psy.Error as e:
            print e.pgerror

        # now that we have added the tree info, update the study record
        # with the json data (minus the tree info)
        del nexml['treesById']
        studyjson = json.dumps(nexml)
        sqlstring = ("UPDATE {tablename} "
            "SET data=%s "
            "WHERE id=%s;"
            .format(tablename=STUDYTABLE)
        )
        data = (studyjson,study_id)
        cursor.execute(sqlstring,data)
        connection.commit()

        counter+=1
        if (counter%500 == 0):
            print "loaded {n} studies".format(n=counter)

        if (nstudies and counter>=nstudies):
            print "finished inserting",nstudies,"studies"
            break

    # load the tree and study properties
    PROPERTYTABLE = config_dict['tables']['propertytable']
    load_properties(
        connection,
        cursor,
        PROPERTYTABLE,
        study_properties,
        tree_properties)

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
    # and clear data
    try:
        tabledict = config_dict['tables']
        for table in tabledict:
            name = tabledict[table]
            if not setup_db.table_exists(cursor,name):
                raise psy.ProgrammingError("Table {t} does not exist".format(t=name))
        setup_db.clear_tables(connection,cursor,config_dict)
        setup_db.clear_gin_index(connection,cursor,config_dict)
        print "done clearing tables and index"
    except psy.Error as e:
        print e.pgerror

    # data import
    starttime = dt.datetime.now()
    try:
        # TODO: catch peyotl-specific exceptions
        phy = create_phylesystem_obj()
        print "loading nexsons"
        if (args.nstudies):
            load_nexsons(connection,cursor,phy,config_dict,args.nstudies)
        else:
            load_nexsons(connection,cursor,phy,config_dict)
        endtime = dt.datetime.now()
        print "Load time: ",endtime - starttime
        print "indexing JSONB columns in tree and study table"
        setup_db.index_json_columns(connection,cursor,config_dict)
    except psy.Error as e:
        print e.pgerror
    connection.close()
    endtime = dt.datetime.now()
    print "Total load + index time: ",endtime - starttime
