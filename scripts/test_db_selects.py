# run some select tests for timing
import psycopg2 as psy
import simplejson as json
import datetime as dt

# fill these in as they are for your system
STUDYTABLE = 'study'
TREETABLE = 'tree'
DBNAME = 'newoti'
USER = 'pguser'

def iterate_all_studies(cursor):
    sqlstring = ("SELECT studyid,year FROM study;")
    cursor.execute(sqlstring)
    print "returned ",cursor.rowcount,"studies"

def iterate_all_trees(cursor):
    sqlstring = "SELECT * FROM tree;"
    cursor.execute(sqlstring)
    print "returned ",cursor.rowcount,"trees"

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

if __name__ == "__main__":
    connection, cursor = connect()
    starttime = dt.datetime.now()
    try:
        iterate_all_studies(cursor)
        iterate_all_trees(cursor)
    except psy.Error as e:
        print e.pgerror
    connection.close()
    endtime = dt.datetime.now()
    print "Query time: ",endtime - starttime
