import psycopg2 as psy
import sqlalchemy
import datetime as dt
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

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSON,JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import ProgrammingError

from sqlalchemy.orm import (
    relationship,
    )

Base = declarative_base()

###### Table defs ###############################

# association between curators and studies
curator_study_table = Table('curator_study_map', Base.metadata,
    Column('study_id', String, ForeignKey('study.id'), primary_key=True),
    Column('curator_id', Integer, ForeignKey('curator.id'), primary_key=True)
    )

# association between trees and otus
tree_otu_table = Table('tree_otu_map', Base.metadata,
    Column('ott_id', Integer, ForeignKey('otu.id'), primary_key=True),
    Column('tree_id', Integer, ForeignKey('tree.id'), primary_key=True)
    )

class Study(Base):
    __tablename__ = 'study'
    # The studyID is of the form prefix_id, so String, not Int.
    id = Column(String, primary_key=True, index=True)
    year = Column(Integer)
    data = Column(JSONB)
    #trees = relationship('Tree',backref='study')
    # many-to-many study<-->curator relationship
    curators = relationship('Curator',
        secondary=curator_study_table,
        back_populates='studies')

class Tree(Base):
    __tablename__ = 'tree'
    __table_args__ = (
        UniqueConstraint('id','study_id'),
        )
    id = Column(Integer,primary_key=True)
    tree_id = Column(String, nullable=False)
    data = Column(JSONB)
    study_id = Column(String, ForeignKey("study.id"), nullable=False)
    ntips = Column(Integer)
    proposed = Column(Boolean)
    # many-to-many tree<-->otu relationship
    otus = relationship('Otu',
        secondary=tree_otu_table,
        back_populates='trees')

class Curator(Base):
    __tablename__ = 'curator'
    id = Column(Integer,primary_key=True)
    name = Column(String,nullable=False,unique=True)
    # many-to-many study<-->curator relationship
    studies = relationship('Study',
        secondary=curator_study_table,
        back_populates='curators')

class Otu(Base):
    __tablename__='otu'
    id = Column(Integer, primary_key=True)
    name = Column(String,nullable=False)
    trees = relationship('Tree',
        secondary=tree_otu_table,
        back_populates='otus')
