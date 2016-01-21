from sqlalchemy import (
    Table,
    Column,
    Index,
    Integer,
    String,
    Text,
    ForeignKey,
    )

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, back_populates
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

########
# Defining tables
########

# define association between studies and curators
# this directive replaces direct creation of a class for the
# association table
curator_study_table = Table('curator_study_map', Base.metadata,
    Column('study_id', Integer, ForeignKey('study.id'), primary_key=True),
    Column('curator_id', Integer, ForeignKey('curator.id'), primary_key=True)
    )

# study table
# The studyID is of the form prefix_id.
# Class defines and one-to-many relationships with trees
# and a many-to-many relationship with curators
# SQL string:
    # tablestring = ('CREATE TABLE {tablename} '
    #     '(id text PRIMARY KEY, '
    #     'year integer, '
    #     'data jsonb);'
    #     .format(tablename=STUDYTABLE)
    #     )
class Study(Base):
    __tablename__ = 'study'
    id = Column(String, primary_key=True, index=True)
    year = Column(Integer)
    data = Column(JSONB)
    trees = relationship('Tree',backref='study')
    # many-to-many study<-->curator relationship
    curators = relationship('Curator',
        secondary=curator_study_table,
        back_populates='studies')

# tree table
# treeid is a auto-incremented integer
# SQL string:
    # tablestring = ('CREATE TABLE {tablename} '
    #     '(id serial PRIMARY KEY, '
    #     'tree_label text NOT NULL, '
    #     'study_id text REFERENCES study (id), '
    #     'UNIQUE (tree_label,study_id));'
    #     .format(tablename=TREETABLE)
    #     )
class Tree(Base):
    __tablename__ = 'tree'
    __table_args__ = (
        UniqueConstraint('id','study_id'),
        )
    id = Column(Integer,primary_key=True)
    tree_label = Column(String, nullable=False)
    study_id = Column(String, ForeignKey("study.id"), nullable=False)

# curator table
# Currently only store curator name in nexsons, which give
# no guarantee about uniqueness or stability
# Therefore use auto-incremented id - could later add github username
# SQL string:
    # tablestring = ('CREATE TABLE {tablename} '
    #     '(id serial PRIMARY KEY, '
    #     'name text UNIQUE);'
    #     .format(tablename=CURATORTABLE)
    #     )
class Curator(Base):
    __tablename__ = 'curator'
    id = Column(Integer,primary_key=True)
    name = Column(String,nullable=False,unique=True)
    # many-to-many study<-->curator relationship
    studies = relationship('Study',
        secondary=curator_study_table,
        back_populates='curators')


# otu-tree table ('what otus are in which trees?')
# SQL string:
    # tablestring = ('CREATE TABLE {tablename} '
    #     '(tree_id int REFERENCES tree (id), '
    #     'ott_id int);'
    #     .format(tablename=OTUTABLE)
    #     )
class Otu(Base):
    __tablename__='otu'
    tree_id = Column(Integer, ForeignKey("tree.id"), nullable=False)
    ott_id = Column(Integer, nullable=False)
