# run some simple select tests
import psycopg2 as psy
import simplejson as json
import argparse
import yaml
import setup_db

def find_all_studies(cursor,config_obj):
    STUDYTABLE = config_obj.get('database_tables','studytable')
    sqlstring = "SELECT id FROM {t};".format(t=STUDYTABLE)
    cursor.execute(sqlstring)
    print "returned",cursor.rowcount,"studies"

def find_all_trees(cursor,config_obj):
    TREETABLE = config_obj.get('database_tables','treetable')
    sqlstring = "SELECT tree_id FROM {t};".format(t=TREETABLE)
    cursor.execute(sqlstring)
    print "returned",cursor.rowcount,"trees"

def find_all_curators(cursor,config_obj):
    CURATORTABLE = config_obj.get('database_tables','curatortable')
    sqlstring = "SELECT * FROM {t};".format(t=CURATORTABLE)
    cursor.execute(sqlstring)
    print "returned",cursor.rowcount,"curators"

def find_all_taxa(cursor,config_obj):
    TAXONOMYTABLE = config_obj.get('database_tables','otttable')
    sqlstring = "SELECT * FROM {t};".format(t=TAXONOMYTABLE)
    cursor.execute(sqlstring)
    print "returned",cursor.rowcount,"taxa"

def find_properties(cursor,config_obj):
    PROPERTYTABLE = config_obj.get('database_tables','propertytable')
    sqlstring = "SELECT * FROM {t} where type='study';".format(t=PROPERTYTABLE)
    cursor.execute(sqlstring)
    print "returned",cursor.rowcount,"study properties"
    sqlstring = "SELECT * FROM {t} where type='tree';".format(t=PROPERTYTABLE)
    cursor.execute(sqlstring)
    print "returned",cursor.rowcount,"tree properties"

def connect(config_obj):
    conn = cursor = None  # not sure of exception intent
    try:
        DBNAME = config_obj.get('connection_info','dbname')
        USER = config_obj.get('connection_info','dbuser')
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
        help='path to the development.ini file'
        )
    args = parser.parse_args()

    # read config variables
    config_obj = setup_db.read_config(args.configfile)

    connection, cursor = setup_db.connect(config_obj)

    try:
        find_all_studies(cursor,config_obj)
        find_all_trees(cursor,config_obj)
        find_all_curators(cursor,config_obj)
        find_all_taxa(cursor,config_obj)
        find_properties(cursor,config_obj)
    except psy.Error as e:
        print e.pgerror
    connection.close()
