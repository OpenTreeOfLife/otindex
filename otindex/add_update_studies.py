from pyramid.httpexceptions import HTTPNotFound
from sqlalchemy.orm import aliased

import re, json, logging

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

_LOG = logging.getLogger(__name__)

def add_study(study_id):
    _LOG.debug('adding study {s}'.format(s=study_id))

    # get latest version of nexson
    # location of repo (test vs dev) dependent on peyotl config
    phy = create_phylesystem_obj()
    try:
        studyobj = phy.get_study(study_id)['data']
    except:
        _LOG.debug('did not find study {s} in phylesystem'.format(s=study_id))
        raise HTTPNotFound("Study {s} not found in phylesystem".format(s=study_id))
    nexml = get_nexml_el(studyobj)
    proposedTrees = nexml.get('^ot:candidateTreeForSynthesis')
    if proposedTrees is None:
        proposedTrees = []

    # create a new Study object
    new_study = Study(id=study_id)
    DBSession.add(new_study)

    # update with treebase id, if exists
    datadeposit = nexml.get('^ot:dataDeposit')
    if (datadeposit):
        url = datadeposit['@href']
        if (url):
            pattern = re.compile(u'.+TB2:(.+)$')
            matchobj = re.match(pattern,url)
            if (matchobj):
                tb_id = matchobj.group(1)
                new_study.treebase_id=tb_id

    # get curator(s), noting that ot:curators might be a
    # string or a list
    c = nexml.get('^ot:curatorName')
    # create list of curator objects
    curator_list=[]
    if (isinstance(c,basestring)):
        curator_list.append(c)
    else:
        curator_list = c
    for curator in curator_list:
        test_c = DBSession.query(Curator).filter(Curator.name==curator).first()
        if test_c:
            _LOG.debug("curator {c} already exists".format(c=curator))
            #DBSession.add(curator)
            new_study.curators.append(test_c)
        else:
            _LOG.debug("curator {c} does not yet exist".format(c=curator))
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
    ntrees = 0
    for trees_group_id, tree_id, tree in iter_trees(studyobj):
        _LOG.debug(' tree : {t}'.format(t=tree_id))
        ntrees+=1
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
                    # _LOG.debug(' mapped ottID: {m}'.format(m=ottID))
                    # check that this exists in the taxonomy
                    # (it might not, if the ID has been deprecated)
                    taxon = DBSession.query(Taxonomy).filter(
                        Taxonomy.id==ottID
                        ).first()
                    if taxon:
                        lineage = get_lineage(ottID)
                        _LOG.debug(' lineage of {m} = {l}'.format(m=ottID,l=lineage))
                        for t in lineage:
                            ottIDs.add(t)
        new_tree.ntips = ntips
        for t in ottIDs:
            taxon = DBSession.query(Taxonomy).filter(
                Taxonomy.id==t
                ).first()
            # _LOG.debug(' adding {t},{n} to tree {tid}'.format(
            #     t=t,
            #     n=taxon.name,
            #     tid=tree_id)
            #     )
            new_tree.otus.append(taxon)

        # add the tree
        DBSession.add(new_tree)

    # now that we have added the tree info, update the study record
    # with the json data (minus the tree info)
    del nexml['treesById']
    studyjson = json.dumps(nexml)
    new_study.data=studyjson
    new_study.ntrees = ntrees

def create_phylesystem_obj():
    # create connection to phylesystem
    phy = PhylesystemAPI()
    return phy

# If the curator(s) associated with this study are *only* associated with
# this study, delete the curator(s)
def deleteOrphanedCurators(study_id):
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
            _LOG.debug("deleting orphan curator {i} for study {s}".format(i=curator_id,s=study_id))
            DBSession.delete(
                DBSession.query(Curator).filter(
                    Curator.id==curator_id
                ).one()
            )

# should only be called after determining that study exists
def delete_study(study_id):
    study = DBSession.query(Study).filter(
        Study.id == study_id
    ).first()
    # check for to-be-orphaned curators
    deleteOrphanedCurators(study_id)
    DBSession.delete(study)
    DBSession.flush()

# get the lineage from this ID back to the root node
def get_lineage(ott_id):
    taxa_in_lineage=[]
    lineage = DBSession.query(
        Taxonomy.id,
        Taxonomy.name,
        Taxonomy.parent).filter(
            Taxonomy.id==ott_id
        ).cte(name="lineage",recursive=True)

    ott_alias = aliased(Taxonomy,name='tid')
    lineage_alias = aliased(lineage,name='lid')

    lineage = lineage.union_all(
        DBSession.query(
            ott_alias.id,
            ott_alias.name,
            ott_alias.parent
        ).filter(
            ott_alias.id==lineage_alias.c.parent
        )
    )
    q = DBSession.query(lineage.c.id).all()
    for row in q:
        taxa_in_lineage.append(row.id)
        # t = DBSession.query(Taxonomy).filter(Taxonomy.id==row.id).first()
        # taxa_in_lineage.append(t)
    return taxa_in_lineage

# URL is a raw github URL to a study
# e.g. https://github.com/OpenTreeOfLife/phylesystem-1/blob/master/study/ot_02/ot_302/ot_302.json
def get_study_id_from_url(url):
    # pattern is {stuff at start of URL}/{prefix}_{numerical_id}.json
    # where prefix is 'ot' or 'pg'
    pattern = re.compile(u'.+/([a-z][a-z]_\d+).json$')
    matchobj = re.match(pattern,url)
    if (matchobj):
        return matchobj.group(1)
    else:
        raise HTTPNotFound("could not find study_id in URL {u}".format(u=url))

# called directly by view add_update_studies_v3
def remove_study(studyid):
    study_id = studyid
    try:
        if studyid.startswith('http'):
            study_id = get_study_id_from_url(studyid)
    except HTTPNotFound:
        raise
    if study_exists(study_id):
        _LOG.debug("removing study {s}".format(s=study_id))
        delete_study(study_id)
    else:
        _LOG.debug("did not find study {s} in database; cannot delete".format(s=study_id))
        raise HTTPNotFound("study {s} not found in database".format(s=study_id))

# check if study exists in DB
def study_exists(study_id):
    study = DBSession.query(Study.id).filter(Study.id==study_id).first()
    if study:
        return True
    else:
        return False

# called directly by view remove_studies_v3
def update_study(studyid):
    try:
        study_id = studyid
        if studyid.startswith('http'):
            study_id = get_study_id_from_url(studyid)
        # delete if already exists
        if (study_exists(study_id)):
            delete_study(study_id)
        #with DBSession.no_autoflush:
        add_study(study_id)
    except Exception:
        raise
