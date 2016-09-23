# run some simple select tests
import psycopg2 as psy
import simplejson as json
import argparse
import yaml

def find_all_studies(cursor,config_dict):
    STUDYTABLE = config_dict['tables']['studytable']
    sqlstring = "SELECT id FROM {t};".format(t=STUDYTABLE)
    cursor.execute(sqlstring)
    print "returned",cursor.rowcount,"studies"

def find_all_trees(cursor,config_dict):
    TREETABLE = config_dict['tables']['treetable']
    sqlstring = "SELECT tree_id FROM {t};".format(t=TREETABLE)
    cursor.execute(sqlstring)
    print "returned",cursor.rowcount,"trees"

def find_all_curators(cursor,config_dict):
    CURATORTABLE = config_dict['tables']['curatortable']
    sqlstring = "SELECT * FROM {t};".format(t=CURATORTABLE)
    cursor.execute(sqlstring)
    print "returned",cursor.rowcount,"curators"

def find_all_taxa(cursor,config_dict):
    TAXONOMYTABLE = config_dict['tables']['otttable']
    sqlstring = "SELECT * FROM {t};".format(t=TAXONOMYTABLE)
    cursor.execute(sqlstring)
    print "returned",cursor.rowcount,"taxa"

def find_all_otus(cursor,config_dict):
    OTUTABLE = config_dict['tables']['otutable']
    sqlstring = "SELECT * FROM {t};".format(t=OTUTABLE)
    cursor.execute(sqlstring)
    print "returned",cursor.rowcount,"otus"

def find_properties(cursor,config_dict):
    PROPERTYTABLE = config_dict['tables']['propertytable']
    sqlstring = "SELECT * FROM {t} where type='study';".format(t=PROPERTYTABLE)
    cursor.execute(sqlstring)
    print "returned",cursor.rowcount,"study properties"
    sqlstring = "SELECT * FROM {t} where type='tree';".format(t=PROPERTYTABLE)
    cursor.execute(sqlstring)
    print "returned",cursor.rowcount,"tree properties"

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

if __name__ == "__main__":
    print "testing DB selects"
    parser = argparse.ArgumentParser(description='simple DB select tests')
    parser.add_argument('configfile',
        help='path to the config file'
        )
    args = parser.parse_args()

    # read config variables
    config_dict={}
    with open(args.configfile,'r') as f:
        config_dict = yaml.safe_load(f)

    connection, cursor = connect(config_dict)
    try:
        find_all_studies(cursor,config_dict)
        find_all_trees(cursor,config_dict)
        find_all_curators(cursor,config_dict)
        #find_all_otus(cursor,config_dict)
        find_all_taxa(cursor,config_dict)
        find_properties(cursor,config_dict)
    except psy.Error as e:
        print e.pgerror
    connection.close()
