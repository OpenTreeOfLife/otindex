from sqlalchemy import (
    Table,
    Column,
    Index,
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    )

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    )

# Update for breaking changes in zope.sqlalchemy 1.2, see details at
# <https://github.com/zopefoundation/zope.sqlalchemy/blob/master/CHANGES.rst#12-2019-10-17>
from zope.sqlalchemy import register
DBSession = scoped_session(sessionmaker())
register(DBSession)

Base = declarative_base()

################################################################
# Defining tables
# Changes to table structure must be copied to setup scripts:
# ../scripts/setup_db.py
# ../scripts/load_nexson.py
################################################################

# define association between studies and curators
# this directive replaces direct creation of a class for the
# association table
curator_study_table = Table('curator_study_map', Base.metadata,
    Column('study_id', String, ForeignKey('study.id'), primary_key=True),
    Column('curator_id', Integer, ForeignKey('curator.id'), primary_key=True)
    )

# association between trees and otus
tree_otu_table = Table('tree_otu_map', Base.metadata,
    Column('ott_id', Integer, ForeignKey('taxonomy.id'), primary_key=True),
    Column('tree_id', Integer, ForeignKey('tree.id'), primary_key=True)
    )

# study table
# Class defines and one-to-many relationships with trees
# and a many-to-many relationship with curators.
# Changes here should also be reflects in otindex/scripts/setup_db.py
# SQL string:
    # tablestring = ('CREATE TABLE {tablename} '
    #     '(id text PRIMARY KEY, '
    #     'year integer, '
    #     'data jsonb);'
    #     .format(tablename=STUDYTABLE)
    #     )
class Study(Base):
    __tablename__ = 'study'
    # The studyID is of the form prefix_id, so String, not Int.
    id = Column(String, primary_key=True, index=True)
    ntrees = Column(Integer)
    treebase_id = Column(String)
    data = Column(JSONB)
    # one-to-many relationship with Tree
    trees = relationship("Tree",
        back_populates="study",
        cascade="all, delete-orphan")
    # many-to-many study<-->curator relationship
    curators = relationship('Curator',
        secondary=curator_study_table,
        back_populates='studies')

# tree table
# treeid is a auto-incremented integer
# also defines a many-to-many relationship with otus
# SQL string:
    # tablestring = ('CREATE TABLE {tablename} '
    #     '(id serial PRIMARY KEY, '
    #     'tree_id text NOT NULL, '
    #     'ntips Integer, '
    #     'synthStatus Enum("proposed","included","none"), '
    #     'data jsonb, '
    #     'study_id text REFERENCES study (id), '
    #     'UNIQUE (tree_id,study_id));'
    #     .format(tablename=TREETABLE)
    #     )
class Tree(Base):
    __tablename__ = 'tree'
    __table_args__ = (
        UniqueConstraint('id','study_id'),
    )
    id = Column(Integer,primary_key=True)
    tree_id = Column(String, nullable=False)
    data = Column(JSONB)
    study_id = Column(String, ForeignKey("study.id"), nullable=False)
    # many-to-one relationship with Study
    study = relationship("Study", back_populates="trees")
    ntips = Column(Integer)
    proposed = Column(Boolean)
    # many-to-many tree<-->otu relationship
    otus = relationship('Taxonomy',
        secondary=tree_otu_table,
        back_populates='trees')

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

# taxonomy table; will replace otu table
# also defines many-to-many relationships with trees
# SQL string:
# tablestring = 'CREATE TABLE {tablename} '
#     '(ott_id int PRIMARY KEY, '
#     'ott_name text, '
#     'rank text, '
#     'parent int);
class Taxonomy(Base):
    __tablename__ = 'taxonomy'
    id = Column(Integer, primary_key=True)
    name = Column(String,nullable=False)
    parent = Column(Integer)
    # many-to-many relationship with trees
    trees = relationship('Tree',
        secondary=tree_otu_table,
        back_populates='otus')
    # one-to-many relationship with synonyms
    synonyms = relationship("Synonym", back_populates="taxon",cascade="all, delete-orphan")

# synonym table
# tablestring = ('CREATE TABLE {tablename} '
#     '(ott_id int REFERENCES taxonomy (ott_id) ON DELETE CASCADE, '
#     'synonym text);'
#     .format(tablename=SYNONYMTABLE)
# )
class Synonym(Base):
    __tablename__='synonym'
    id = Column(Integer,primary_key=True)
    ott_id = Column(Integer,ForeignKey("taxonomy.id"))
    synonym = Column(String)
    # many-to-one relationship with Taxonomy
    taxon = relationship("Taxonomy", back_populates="synonyms")

# property table
# tablestring = ('CREATE TABLE {tablename} '
#     '(id serial PRIMARY KEY, '
#     'property text, '
#     'prefix text, '
#     'type text, '
#     'UNIQUE (property,type));'
#     .format(tablename=PROPERTYTABLE)
# )
class Property(Base):
    __tablename__='property'
    __table_args__ = (
        UniqueConstraint('property','type'),
        )
    id = Column(Integer,primary_key=True)
    property = Column(String, nullable=False)
    prefix = Column(String)
    type = Column(String, nullable=False)

# GIN indexes on jsonb columns
Index('tree_ix_data_gin', Tree.data, postgresql_using='gin')
Index('study_ix_data_gin', Study.data, postgresql_using='gin')
