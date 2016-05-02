# helper functions for find_trees queries

from .models import (
    DBSession,
    Study,
    Tree,
    Otu,
    )

import simplejson as json
import sqlalchemy
from sqlalchemy.dialects.postgresql import JSON,JSONB
from sqlalchemy import Integer
from sqlalchemy.exc import ProgrammingError
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest

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
                    get_study_properties(studyid,studydict)
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


# find_trees methods also return info about studies
# this method gets the study-level fields
def get_study_properties(studyid,studydict):
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
def get_tree_property_list(version=3):
    tree_props= [
        "ot:treebaseOTUId", "ot:nodeLabelMode", "ot:originalLabel",
        "ot:ottTaxonName", "ot:inferenceMethod", "ot:tag",
        "ot:comment", "ot:treebaseTreeId", "ot:branchLengthDescription",
        "ot:treeModified", "ot:studyId", "ot:branchLengthTimeUnits",
        "ot:ottId", "ot:branchLengthMode", "ot:treeLastEdited",
        "ot:nodeLabelDescription"
        ]
    return tree_props

# returns an (unfiltered) tree query object with either the set of
# verbose=true or verbose=false fields. Query not yet run.
def get_tree_query_object(verbose):
    query_obj = None
    if (verbose):
        # assigning labels like this makes it easy to build the response json
        # but can't directly access any particular item via the label,
        # i.e result.ot:studyId because of ':' in label
        query_obj = DBSession.query(
            Tree.tree_label.label('ot:treeId'),
            Tree.study_id.label('ot:studyId'),
            Tree.data[('^ot:branchLengthMode')].label('ot:branchLengthMode'),
            Tree.data[('^ot:branchLengthDescription')].label('ot:branchLengthDescription')
        )
    else:
        query_obj = DBSession.query(
            Tree.study_id.label('ot:studyId'),
            Tree.tree_label.label('ot:treeId')
        )
    return query_obj

# # find studies by curators; uses Study-Curator association table
# def query_studies_by_curator(query_obj,property_value):
#     filtered = query_obj.filter(
#         Study.curators.any(name=property_value)
#         )
#     return filtered

# looking for a value in a list, e.g. ot:tag
def query_by_tag(query_obj,property_value):
    property_type = '^ot:tag'
    filtered = query_obj.filter(
        Tree.data.contains({property_type:[property_value]})
    )
    return filtered

# def query_fulltext(query_obj,property_type,property_value):
#     property_type = '^'+property_type
#     # add wildcards to the property_value
#     property_value = '%'+property_value+'%'
#     filtered = query_obj.filter(
#         Study.data[
#             property_type
#         ].astext.ilike(property_value)
#     )
#     return filtered
#
# # find studies in cases where the property_value is an int
# def query_studies_by_integer_values(query_obj,property_type,property_value):
#     property_type = '^'+property_type
#     filtered = query_obj.filter(
#         Study.data[
#             (property_type)
#         ].cast(sqlalchemy.Integer) == property_value
#         )
#     return filtered

# filter query to return only trees that match property_type and
# property_value
def query_trees(verbose,property_type,property_value):
    resultlist = []

    # get the base (unfiltered) query object
    query_obj = get_tree_query_object(verbose)
    filtered = None

    # study id is straightforward
    if property_type == "ot:studyId":
        filtered = query_obj.filter(Tree.study_id == property_value)

    # curator uses study-curator association table
    # elif property_type == "ot:curatorName":
    #     filtered = query_studies_by_curator(query_obj,property_value)
    #
    # # year and focal clade are in json, need to cast value to int
    # elif property_type == "ot:studyYear" or property_type == "ot:focalClade":
    #     filtered = query_studies_by_integer_values(
    #         query_obj,
    #         property_type,
    #         property_value)
    #
    # # value of ot:studyPublication and ot:dataDeposit
    # # is a dict with key '@href'
    # elif property_type == "ot:studyPublication" or property_type == "ot:dataDeposit":
    #     property_type = '^'+property_type
    #     filtered = query_obj.filter(
    #         Study.data[
    #             (property_type,'@href')
    #         ].astext == property_value
    #         )
    #
    # elif property_type == "ot:studyPublicationReference" or property_type == "ot:comment":
    #     filtered = query_fulltext(query_obj,property_type,property_value)

    # tag is a list
    elif property_type == "ot:tag":
        filtered = query_by_tag(query_obj,property_value)

    # all other property types are strings contained in json
    else:
        property_type = '^'+property_type
        filtered = query_obj.filter(
            Tree.data[
                (property_type)
            ].astext == property_value
            )

    resultslist = []
    studydict = {}
    try:
        for row in filtered.all():
            treedict = row._asdict()
            studyid = treedict['ot:studyId']
            if not studyid in studydict:
                # if this is the first time we have seen this study,
                # get either the studyid or the study properties and
                # add a blank list for the trees
                if (verbose):
                    get_study_properties(studyid,studydict)
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
