# tests for database setup
import psycopg2 as psy
import simplejson as json
import datetime as dt
import setup_db
import unittest

class TestDatabaseSetup():
    def __init__(self):
        self.config_obj = {}
        self.connection_tuple = ()

    def setUp(self):
        # read config file
        self.config_obj = setup_db.read_config('../../development.ini')
        self.connection_tuple = setup_db.connect(self.config_obj)

    def tearDown(self):
        connection,cursor = self.connection_tuple
        connection.close()

    def testCreateTable(self):
        connection,cursor = self.connection_tuple
        tablename='test'
        tablestring = ('CREATE TABLE {name} '
            '(id text PRIMARY KEY, '
            'year integer, '
            'data jsonb);'
            .format(name=tablename)
            )
        setup_db.create_table(connection,cursor,tablename,tablestring)
        assert setup_db.table_exists(cursor, tablename) == True

    def testDeleteTable(self):
        connection,cursor = self.connection_tuple
        tablename='test'
        assert setup_db.table_exists(cursor, tablename) == True
        setup_db.delete_table(connection,cursor,tablename)
        assert setup_db.table_exists(cursor, tablename) == False
