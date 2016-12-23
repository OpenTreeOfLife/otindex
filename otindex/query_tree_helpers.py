# helper functions for find_trees queries

from .models import (
    DBSession,
    Study,
    Tree,
    Taxonomy,
    Property,
    )

import simplejson as json
import sqlalchemy
import logging
from sqlalchemy.dialects.postgresql import JSON,JSONB
from sqlalchemy.exc import ProgrammingError
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest

_LOG = logging.getLogger(__name__)

# get all trees, no filtering
# returns them grouped by study
def get_all_trees(verbose):
    resultlist = []
    query_obj = get_tree_query_object(verbose)
    resultslist = []
    studydict = {}

    try:
        for row in query_obj.all():
            treedict = row._asdict()
            studyid = treedict['ot:studyId']
            if not studyid in studydict:
                # if this is the first time we have seen this study,
                # get either the studyid or the study properties and
                # add a blank list for the trees
                if (verbose):
                    get_study_return_props(studyid,studydict)
                else:
                    studydict[studyid] = {'ot:studyId':studyid}
                studydict[studyid]['matched_trees'] = []
            # add the tree properties to the list of matched trees
            studydict[studyid]['matched_trees'].append(treedict)
        for k,v in studydict.items():
            resultslist.append(v)
    except ProgrammingError as e:
        raise HTTPBadRequest()

    return resultslist

# given a taxon name, return the OTT ID, if it exists
def get_ott_id(ottname):
    query_obj = DBSession.query(
        Taxonomy.id
    ).filter(Taxonomy.name == ottname)

    # should only be one row
    # should test for >1 row and throw error?
    row = query_obj.first()
    if row is not None:
        return row.id
    else:
        return None

# given a property, returns the property with prefix
def get_prop_with_prefix(prop):
    query_obj = DBSession.query(Property.prefix).filter(
        Property.property == prop
    ).first()
    return query_obj.prefix+prop

# find_trees methods also return info about studies
# this method gets the study-level fields
def get_study_return_props(studyid,studydict):
    slist =[
        "^ot:studyPublicationReference","^ot:curatorName",
        "^ot:studyYear","^ot:focalClade","^ot:focalCladeOTTTaxonName",
        "^ot:dataDeposit","^ot:studyPublication"
        ]
    # assigning labels like this makes it easy to build the response json
    # but can't directly access any particular item via the label,
    # i.e result.ot:studyId because of ':' in label
    query_obj = DBSession.query(
        Study.id.label('ot:studyId'),
        Study.data[(slist[0])].label('ot:studyPublicationReference'),
        Study.data[(slist[1])].label('ot:curatorName'),
        Study.data[(slist[2])].label('ot:studyYear'),
        Study.data[(slist[3])].label('ot:focalClade'),
        Study.data[(slist[4])].label('ot:focalCladeOTTTaxonName'),
        Study.data[(slist[5])].label('ot:dataDeposit'),
        Study.data[(slist[6])].label('ot:studyPublication'),
    ).filter(
        Study.id == studyid
    )

    # should only be one row
    resultdict = {}
    for row in query_obj.all():
        for k,v in row._asdict().items():
            if v is not None:
                resultdict[k]=v
    studydict[studyid] = resultdict
    return studydict

# get the list of searchable properties
# v3 list pruned down to only those implemented in v3
def get_tree_property_list():
    properties = []
    query_obj = DBSession.query(Property.property).filter(
        Property.type=='tree'
    ).all()
    for row in query_obj:
        properties.append(row.property)
    # now add the non-JSON properties
    properties.append('ot:ottId')
    properties.append('ot:ottTaxonName')
    properties.append('ot:studyId')
    properties.append("ntips")
    #properties.append("proposed")
    return properties

# returns an (unfiltered) tree query object with either the set of
# verbose=true or verbose=false fields. Query not yet run.
def get_tree_query_object(verbose):
    query_obj = None
    if (verbose):
        # assigning labels like this makes it easy to build the response json
        # but can't directly access any particular item via the label,
        # i.e result.ot:studyId because of ':' in label
        query_obj = DBSession.query(
            Tree.tree_id.label('ot:treeId'),
            Tree.study_id.label('ot:studyId'),
            Tree.proposed.label('ot:proposedForSynthesis'),
            Tree.data[('@label')].label('@label'),
            Tree.data[('^ot:branchLengthMode')].label('ot:branchLengthMode'),
            Tree.data[('^ot:branchLengthDescription')].label('ot:branchLengthDescription')
        )
    else:
        query_obj = DBSession.query(
            Tree.study_id.label('ot:studyId'),
            Tree.tree_id.label('ot:treeId')
        )
    return query_obj

def is_deprecated_property(prop):
    deprecated_oti_properties = [ "ot:treebaseOTUId", "ot:originalLabel", "oti_tree_id", "ot:treebaseTreeId", "ot:comment", "ot:treeModified", "ot:branchLengthTimeUnits", "is_deprecated", "ot:treeLastEdited" ]
    if prop in deprecated_oti_properties:
        return True
    else:
        return False

# find trees by otu ids; uses Tree-Taxonomy association table
def query_trees_by_ott_id(query_obj,property_value):
     filtered = query_obj.filter(
         Tree.otus.any(id=property_value)
         )
     return filtered

# looking for a value in a list, e.g. ot:tag
def query_trees_by_tag(query_obj,property_value):
    property_type = '^ot:tag'
    filtered = query_obj.filter(
        Tree.data.contains({property_type:[property_value]})
    )
    return filtered

def query_fulltext(query_obj,property_type,property_value):
     property_type = get_prop_with_prefix(property_type)
     # add wildcards to the property_value
     property_value = '%'+property_value+'%'
     filtered = query_obj.filter(
         Study.data[
             property_type
         ].astext.ilike(property_value)
     )
     return filtered

def build_json_response(filtered,verbose):
    resultslist = []
    studydict = {}
    # run the query and build the response json
    for row in filtered.all():
        treedict = row._asdict()
        studyid = treedict['ot:studyId']
        if not studyid in studydict:
            # if this is the first time we have seen this study,
            # get either the studyid or the study properties and
            # add a blank list for the trees
            if (verbose):
                get_study_return_props(studyid,studydict)
            else:
                studydict[studyid] = {'ot:studyId':studyid}
            studydict[studyid]['matched_trees'] = []
        # add the tree properties to the list of matched trees
        studydict[studyid]['matched_trees'].append(treedict)
    for k,v in studydict.items():
        resultslist.append(v)
    return resultslist

# filter query to return only trees that match property_type and
# property_value
def query_trees(verbose,property_type,property_value):
    resultlist = []
    _LOG.debug("querying trees by {p} : {v}".format(p=property_type,v=property_value))
    # get the base (unfiltered) query object
    query_obj = get_tree_query_object(verbose)
    filtered = None

    # study id is straightforward; is table column
    if property_type == "ot:studyId":
        filtered = query_obj.filter(Tree.study_id == property_value)

    # ntips is a table column
    elif property_type == "ntips":
        filtered = query_obj.filter(Tree.ntips == property_value)

    # as is candidateForSynthesis - mapped to proposed
    elif property_type == "ot:candidateTreeForSynthesis":
        filtered = query_obj.filter(Tree.proposed == property_value)

    # otu uses tree-otu association table
    elif property_type == "ot:ottTaxonName":
        # get OTT ID for this name
        ott_id = get_ott_id(property_value)
        if ott_id is not None:
            filtered = query_trees_by_ott_id(ott_id)
        else:
            # TODO: helpful error message about taxon name not found
            raise HTTPNotFound()

    elif property_type == "ot:ottId":
        filtered = query_trees_by_ott_id(query_obj,property_value)

    # tag is a list
    elif property_type == "ot:tag":
        filtered = query_trees_by_tag(query_obj,property_value)

    # all other property types are strings contained in json
    # also, if property_type = ot:inferenceMethod, change to
    # ot:curatedType
    else:
        # there are two properties where API docs do not match
        # property name in nexson
        if property_type == "ot:branchLengthTimeUnits":
            property_type = "ot:branchLengthTimeUnit"
        if property_type == "ot:inferenceMethod":
            property_type = "ot:curatedType"
        property_type = get_prop_with_prefix(property_type)
        filtered = query_obj.filter(
            Tree.data[
                (property_type)
            ].astext == property_value
            )
    try:
        resultslist = build_json_response(filtered,verbose)
        return resultslist
    except ProgrammingError as e:
        raise HTTPBadRequest()
