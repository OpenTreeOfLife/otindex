# test delete logic
# does deleting a study also delete orphan curators, trees, etc?

import psycopg2 as psy
import sqlalchemy

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSON,JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import ProgrammingError

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    )

from dev_models import (
    Study,
    Tree,
    Otu,
    Curator,
)

# if there are OTUs only used by trees in this study, delete them
def deleteOrphanedOtus(session,study_id):
    # get the trees for this study
    trees = session.query(Tree.tree_id).filter(
        Tree.study_id == study_id
    ).all()
    for t in trees:
        tid = t.tree_id
        # get the otus for this tree
        otus = session.query(Otu.id).filter(
            Otu.trees.any(tree_id=tid)
        ).all()
        for o in otus:
            oid = o.id
            treecount = session.query(Tree.id).filter(
                Tree.otus.any(id=oid)
            ).count()
            if treecount==1:
                # only used in this tree
                #print "deleting otu {o} only used in tree {t}".format(
                #     o=oid,t=tid
                # )
                session.delete(
                    session.query(Otu).filter(
                        Otu.id==oid
                    ).one()
                )
                session.commit()

def deleteOrphanedCurators(session,study_id):
    # get curators that edited this study
    curators = session.query(Curator.id).filter(
        Curator.studies.any(id=study_id)
    ).all()
    for c in curators:
        curator_id = c.id
        studies = session.query(Study.id).filter(
            Study.curators.any(id=c.id)
        )
        # if there is only one study edited by this curator
        if (studies.count()==1):
            #print "deleting curator {i}".format(i=curator_id)
            session.delete(
                session.query(Curator).filter(
                    Curator.id==curator_id
                ).one()
            )
            session.commit()

def deleteStudy(session,study_id):
    print "deleting study",study_id
    study = session.query(Study).filter(
        Study.id == study_id
    ).one()
    if (study):
        print "found study {s}".format(s=study_id)
        # check for to-be-orphaned curators
        # if the curator(s) associated with this study are only associated with
        # this study, delete the curator
        deleteOrphanedCurators(session,study_id)
        deleteOrphanedOtus(session,study_id)
        session.delete(study)
        session.commit()
    else:
        print "study id {s} not found".format(s=study_id)

def count_all(session):
    find_all_studies(session)
    find_all_trees(session)
    find_all_curators(session)
    find_all_otus(session)

def find_all_studies(session):
    query_obj = session.query(
        Study.id,
    ).all()
    print "returned",len(query_obj),"studies"

def find_all_trees(session):
    query_obj = session.query(
        Tree.study_id,
        Tree.tree_id
    ).all()
    print "returned",len(query_obj),"trees"

def find_all_curators(session):
    query_obj = session.query(
        Curator.id
    ).all()
    print "returned",len(query_obj),"curators"

def find_all_otus(session):
    query_obj = session.query(
        Otu.id
    ).all()
    print "returned",len(query_obj),"otus"

def getOneStudy(session):
    query_obj = session.query(Study.id).first()
    return query_obj.id

if __name__ == "__main__":
    connection_string = 'postgresql://postgres@localhost/otindex'
    db = sqlalchemy.create_engine(connection_string)
    engine = db.connect()
    meta = sqlalchemy.MetaData(engine)
    SessionFactory = sessionmaker(engine)
    session = SessionFactory()

    try:
        count_all(session)
        study_id = getOneStudy(session)
        deleteStudy(session,study_id)
        count_all(session)
    except ProgrammingError as e:
        print e.message
