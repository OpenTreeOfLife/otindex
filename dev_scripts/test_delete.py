# test delete logic
# deleting a study requires deleting orphan curators, trees, otus

import psycopg2 as psy
import sqlalchemy
import requests
import simplejson as json
import re

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSON,JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import ProgrammingError

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    )

from peyotl.api import PhylesystemAPI
from peyotl.nexson_syntax import get_nexml_el
from peyotl.nexson_proxy import NexsonProxy
from peyotl.manip import iter_trees

from dev_models import (
    Study,
    Tree,
    Taxonomy,
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
        otus = session.query(Taxonomy.id).filter(
            Taxonomy.trees.any(tree_id=tid)
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
            print "deleting curator {i}".format(i=curator_id)
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
        print "deleting study {s}".format(s=study_id)
        # check for to-be-orphaned curators
        # if the curator(s) associated with this study are only associated with
        # this study, delete the curator
        deleteOrphanedCurators(session,study_id)
        #deleteOrphanedOtus(session,study_id)
        session.delete(study)
        session.commit()
    else:
        print "study id {s} not found".format(s=study_id)

def count_all(session):
    find_all_studies(session)
    find_all_trees(session)
    find_all_curators(session)
    # find_all_otus_in_trees(session)

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

# def find_all_otus_in_trees(session):
#     # count all rows in the tree-taxonomy association table
#     otus = session.query(Taxonomy.ott_id).filter(
#             Taxonomy.trees.any(tree_id=tid)
#         ).all()
#     print "returned",len(query_obj),"otus"

def getOneStudy(session):
    query_obj = session.query(Study.id).first()
    return query_obj.id

# in the API, this takes a raw github URL to a study as argument,
# e.g. https://raw.github.com/OpenTreeOfLife/phylesystem/master/study/10/10.json
# replicates the logic in load_nexsons for loading all studies
def addStudy(session,study_id):
    # get latest version of nexson
    phy = PhylesystemAPI(get_from='local')
    studyobj = phy.get_study(study_id)['data']
    nexml = get_nexml_el(studyobj)
    year = nexml.get('^ot:studyYear')
    proposedTrees = nexml.get('^ot:candidateTreeForSynthesis')
    if proposedTrees is None:
        proposedTrees = []

    # create a new Study object
    new_study = Study(id=study_id,year=year)
    session.add(new_study)
    #session.commit()

    # get curator(s), noting that ot:curators might be a
    # string or a list
    c = nexml.get('^ot:curatorName')
    print ' ot:curatorName: ',c
    # create list of curator objects
    curator_list=[]
    if (isinstance(c,basestring)):
        curator_list.append(Curator(name=c))
    else:
        for i in c:
            curator_list.append(Curator(name=i))
    for curator in curator_list:
        if session.query(Curator).filter(Curator.name==curator.name).first():
            print "curator {c} does not exist".format(c=curator.name)
            #session.add(curator)
            new_study.curators = curator
        else:
            print "curator {c} already exists".format(c=curator.name)
            new_study.curators.append(curator)

    # now add the curator - study association
    #new_study.curators=curator_list
    #session.commit()

    # iterate over trees and insert tree data
    for trees_group_id, tree_id, tree in iter_trees(studyobj):
        print ' tree :' ,tree_id
        nnodes = len(tree.get('nodeById', {}).items())
        proposedForSynth = False
        if (tree_id in proposedTrees):
            proposedForSynth = True
        treejson = json.dumps(tree)
        new_tree = Tree(
            tree_id=tree_id,
            study_id=study_id,
            ntips=nnodes,
            proposed=proposedForSynth,
            data=treejson
            )

        # update with treebase id, if exists
        datadeposit = nexml.get('^ot:dataDeposit')
        if (datadeposit):
            url = datadeposit['@href']
            pattern = re.compile(u'.+TB2:(.+)$')
            matchobj = re.match(pattern,url)
            if (matchobj):
                tb_id = matchobj.group(1)
                new_tree.treebase_id=tb_id
        session.add(new_tree)

    # now that we have added the tree info, update the study record
    # with the json data (minus the tree info)
    del nexml['treesById']
    studyjson = json.dumps(nexml)
    new_study.data=studyjson
    session.commit()

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
        addStudy(session,study_id)
        count_all(session)
    except ProgrammingError as e:
        print e.message
