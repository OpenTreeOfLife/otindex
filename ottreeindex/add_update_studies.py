import re, json

from peyotl.api import PhylesystemAPI
from peyotl.nexson_syntax import get_nexml_el
from peyotl.nexson_proxy import NexsonProxy
from peyotl.manip import iter_trees
from peyotl import gen_otu_dict, iter_node

from .models import (
    DBSession,
    Study,
    Tree,
    Curator,
    Taxonomy,
    )

def add_study(study_id):
    # get latest version of nexson
    print "adding study {s}".format(s=study_id)
    phy = create_phylesystem_obj()
    studyobj = phy.get_study(study_id)['data']
    nexml = get_nexml_el(studyobj)
    year = nexml.get('^ot:studyYear')
    proposedTrees = nexml.get('^ot:candidateTreeForSynthesis')
    if proposedTrees is None:
        proposedTrees = []

    # create a new Study object
    new_study = Study(id=study_id,year=year)
    DBSession.add(new_study)
    #DBSession.commit()

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
        test_c = DBSession.query(Curator).filter(Curator.name==curator).first()
        if test_c:
            print "curator {c} already exists".format(c=curator)
            #DBSession.add(curator)
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
                    taxon = DBSession.query(Taxonomy).filter(
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
        DBSession.add(new_tree)

    # now that we have added the tree info, update the study record
    # with the json data (minus the tree info)
    del nexml['treesById']
    studyjson = json.dumps(nexml)
    new_study.data=studyjson
    # DBSession.commit()

def create_phylesystem_obj():
    # create connection to local phylesystem
    phy = PhylesystemAPI()
    return phy

def deleteOrphanedCurators(study_id):
    # get curators that edited this study
    curators = DBSession.query(Curator.id).filter(
        Curator.studies.any(id=study_id)
    ).all()
    for c in curators:
        curator_id = c.id
        studies = DBSession.query(Study.id).filter(
            Study.curators.any(id=c.id)
        )
        # if there is only one study edited by this curator
        if (studies.count()==1):
            print "deleting curator {i}".format(i=curator_id)
            DBSession.delete(
                DBSession.query(Curator).filter(
                    Curator.id==curator_id
                ).one()
            )
            #DBSession.commit()

def delete_study(study_id):
    study = DBSession.query(Study).filter(
        Study.id == study_id
    ).first()
    if (study):
        print "deleting study {s}".format(s=study_id)
        # check for to-be-orphaned curators
        # if the curator(s) associated with this study are only associated with
        # this study, delete the curator
        deleteOrphanedCurators(DBSession,study_id)
        #deleteOrphanedOtus(DBSession,study_id)
        DBSession.delete(study)
        # DBSession.commit()
    else:
        print "study id {s} not found".format(s=study_id)

# URL is a raw github URL to a study
# e.g. https://github.com/OpenTreeOfLife/phylesystem-1/blob/master/study/ot_02/ot_302/ot_302.json
def update_study(url):
    # get the study_id data from the URL
    pattern = re.compile(u'.+([a-z][a-z]_\d+).json$')
    matchobj = re.match(pattern,url)
    study_id=""
    if (matchobj):
        study_id = matchobj.group(1)
    delete_study(study_id)
    add_study(study_id)
