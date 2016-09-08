# Imports the Open Tree Taxonomy into a postgres database
#   taxonomy.tsv and synonyms.tsv only
# Assumes database already set up. This happends either in initializedb.py
#   if running pyramid app or setup_db.py for testing (both in
#   this same directory)

import datetime as dt
import argparse
import psycopg2 as psy
import csv
import yaml
import io

# other database functions
import setup_db

# peyotl functions for handling the taxonomy
import peyotl.ott as ott

def load_taxonomy_using_copy(connection,cursor,otttable,syntable,path):
    print "Loading taxonomy into memory"
    taxonomy = ott.OTT(ott_loc)
    # get dictionary of ottids:ottnames, noting that the names can be strings
    # or tuples, e.g. (canonical name,synonym,synonym)
    ott_names = taxonomy.ott_id_to_names
    # dictionary of ottid:parent_ottid
    ott_parents = taxonomy.ott_id2par_ott_id
    print "loading {t} names".format(
        t=len(ott_names),
    )
    ott_filename = "ott.csv"
    synonym_filename = "synonyms.csv"
    try:
        #with codecs.open(ott_filename,'w','utf-8') as of:
        # with io.open(ott_filename,'w',encoding='utf-8') as of, io.open(synonym_filename,'w',encoding='utf-8') as sf:
        with open(ott_filename,'w') as of, open(synonym_filename,'w') as sf:
            ofwriter = csv.writer(of)
            sfwriter = csv.writer(sf)
            # header row for ott file
            #of.write(u'ott_id,name,parent_id\n')
            ofwriter.writerow(('id','name','parent'))
            # header row for synonym file
            sfwriter.writerow(('id','synonym'))

            for ott_id in ott_names:
                name = ott_names[ott_id]
                synonyms=[]
                # if names is a tuple, then the first element is the unique name
                # and the others are synonyms
                if (isinstance(name,tuple)):
                    synonyms = name[1:]
                    name = name[0]
                parent_id = ott_parents[ott_id]
                # if this is the root, use -1 as the parent
                if parent_id == None:
                    parent_id = -1
                #of.write(u'{},"{}",{}\n'.format(ott_id,name,parent_id))
                ofwriter.writerow((ott_id,name.encode('utf-8'),parent_id))

                # print synonym data
                for s in synonyms:
                    #sf.write(u'{},"{}"\n'.format(ott_id,s))
                    sfwriter.writerow((ott_id,s.encode('utf-8')))
        of.close()
        sf.close()
    except IOError as (errno,strerror):
        print "I/O error({0}): {1}".format(errno, strerror)

    # import the csv files into the tables
    print "Importing taxonomy files"
    setup_db.import_csv_file(connection,cursor,otttable,ott_filename)
    setup_db.import_csv_file(connection,cursor,syntable,synonym_filename)

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
        print "clearing tables"
        TAXONOMYTABLE = config_dict['tables']['otttable']
        if not setup_db.table_exists(cursor,TAXONOMYTABLE):
            raise psy.ProgrammingError("Table {t} does not exist".format(t=TAXONOMYTABLE))
        setup_db.clear_single_table(connection,cursor,TAXONOMYTABLE)
        SYNONYMTABLE = config_dict['tables']['synonymtable']
        if not setup_db.table_exists(cursor,SYNONYMTABLE):
            raise psy.ProgrammingError("Table {t} does not exist".format(t=SYNONYMTABLE))
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
            load_taxonomy_using_copy(connection,cursor,TAXONOMYTABLE,SYNONYMTABLE,ott_loc)
            endtime = dt.datetime.now()
            print "OTT load time: ",endtime - starttime
    except psy.Error as e:
        print e.pgerror
    connection.close()
