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
from peyotl import gen_otu_dict, iter_node

from dev_models import (
    Study,
    Tree,
    Taxonomy,
    Curator,
)

# in the API, this takes a raw github URL to a study as argument,
# e.g. https://raw.github.com/OpenTreeOfLife/phylesystem/master/study/10/10.json
# replicates the logic in load_nexsons for loading all studies
def addStudy(session,study_id):
    # get latest version of nexson
    print "adding study {s}".format(s=study_id)
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
        curator_list.append(c)
    else:
        curator_list = c
    for curator in curator_list:
        test_c = session.query(Curator).filter(Curator.name==curator).first()
        if test_c:
            print "curator {c} already exists".format(c=curator)
            #session.add(curator)
            new_study.curators.append(test_c)
        else:
            print "curator {c} does no exist".format(c=curator)
            new_study.curators.append(Curator(name=curator))

    # mapped otus in this study
    otu_dict = gen_otu_dict(studyobj)
    # iterate over the OTUs in the study, collecting the mapped
    # ones (oid to ott_id mapping held at the study level)
    mapped_otus = {}
    for oid, o in otu_dict.items():
        ottID = o.get('^ot:ottId')
        if ottID is not None:
            mapped_otus[oid]=ottID

    # iterate over trees and insert tree data
    for trees_group_id, tree_id, tree in iter_trees(studyobj):
        print ' tree :' ,tree_id
        proposedForSynth = False
        if (tree_id in proposedTrees):
            proposedForSynth = True

        treejson = json.dumps(tree)
        new_tree = Tree(
            tree_id=tree_id,
            study_id=study_id,
            proposed=proposedForSynth,
            data=treejson
            )

        # get otus
        ottIDs = set()     # ott ids for this tree
        ntips=0
        for node_id, node in iter_node(tree):
            oid = node.get('@otu')
            # no @otu property on internal nodes
            if oid is not None:
                ntips+=1
                #ottID = mapped_otus[oid]
                if oid in mapped_otus:
                    ottID = mapped_otus[oid]
                    # check that this exists in the taxonomy
                    # (it might not, if the ID has been deprecated)
                    taxon = session.query(Taxonomy).filter(
                        Taxonomy.id==ottID
                        ).first()
                    if taxon:
                        new_tree.otus.append(taxon)
                        ottIDs.add(ottID)
        new_tree.ntips = ntips
        # need to write function for recursive query of Taxonomy table
        #ottIDs = parent_closure(ottIDs,taxonomy)

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
    study = session.query(Study).filter(
        Study.id == study_id
    ).one()
    if (study):
        print "deleting study {s}".format(s=study_id)
        # check for to-be-orphaned curators
        # if the curator(s) associated with this study are only associated with
        # this study, delete the curator
        deleteOrphanedCurators(session,study_id)
        session.delete(study)
        session.commit()
    else:
        print "study id {s} not found".format(s=study_id)

def count_all(session):
    studies = find_all_studies(session)
    trees = find_all_trees(session)
    curators = find_all_curators(session)
    # find_all_otus_in_trees(session)
    return (studies,trees,curators)

def find_all_studies(session):
    study_count = session.query(
        Study.id,
    ).count()
    return study_count

def find_all_trees(session):
    tree_count = session.query(
        Tree.study_id,
        Tree.tree_id
    ).count()
    return tree_count

def find_all_curators(session):
    curator_count = session.query(
        Curator.id
    ).count()
    return curator_count

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
        (s,t,c) = count_all(session)
        print s,t,c
        study_id = getOneStudy(session)
        deleteStudy(session,study_id)
        (s,t,c) = count_all(session)
        print s,t,c
        addStudy(session,study_id)
        (s,t,c) = count_all(session)
        print s,t,c
    except ProgrammingError as e:
        print e.message
