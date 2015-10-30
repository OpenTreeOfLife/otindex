# Imports a directory of json files into a postgres database
# with a column of type 'json' or 'jsonb'

# inspired by https://github.com/JarenGlover/postgres-json-example

import sys,traceback
import datetime as dt
import argparse
import glob
import psycopg2 as psy
import simplejson

# fill these in as they are on your system
TABLE = 'nexson_jsonb'
COLUMN = 'data'
DBNAME = 'newoti'
USER = 'pguser'

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

def get_files():
    parser = argparse.ArgumentParser(description='provide name of json file')
    parser.add_argument('directory', help='directory containing json files to load')
    args = parser.parse_args()
    pattern=args.directory+"/*.json"
    filelist = glob.glob(pattern)
    print "Found {nfiles} files".format(nfiles=len(filelist))
    return filelist

def loadjson(connection,cursor,files):
    for filename in files:
        print filename
        f = open(filename,'r')
        # assuming each file contains a single study
        for line in f:
            # QuotedString escapes single quotes, line breaks, etc
            qline = psy.extensions.QuotedString(line.strip()).getquoted()
            SQL="INSERT INTO %(table)s (%(column)s) VALUES (%(data)s)" % {"table":TABLE, "column":COLUMN, "data":qline}
            cursor.execute(SQL)
            connection.commit()

if __name__ == "__main__":
    connection, cursor = connect()
    starttime = dt.datetime.now()
    print starttime
    loadjson(connection,cursor,get_files())
    connection.close()
    endtime = dt.datetime.now()
    print "Elapsed: ",endtime - starttime
