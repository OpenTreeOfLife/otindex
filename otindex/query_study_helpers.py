# helper functions for the find_studies views

from .models import (
    DBSession,
    Study,
    Tree,
    Curator,
    Property,
    )

import simplejson as json
import sqlalchemy
import logging
from sqlalchemy.dialects.postgresql import JSON,JSONB
from sqlalchemy import Integer
from sqlalchemy.exc import ProgrammingError
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest
from .util import clean_dict_values, get_study_parameters

_LOG = logging.getLogger(__name__)


def is_deprecated_property(prop):
    deprecated_oti_properties = [ "ot:studyModified", "ot:focalCladeOTTId", "ot:studyLastEditor", "ot:focalCladeTaxonName", "ot:studyLabel", "ot:authorContributed", "ot:studyUploaded", "is_deprecated", "ot:candidateTreeForSynthesis" ]
    if prop in deprecated_oti_properties:
        return True
    else:
        return False

# get all trees, no filtering
def get_all_studies(verbose):
    resultlist = []
    query_obj = get_study_query_object(verbose)
    # get results as dict, where keys are the labels set in
    # get_study_query_object
    for row in query_obj.all():
        item = {}
        clean_dict_values(row._asdict(), item)
        resultlist.append(item)
    return resultlist

# given a property, returns the property with prefix
def get_prop_with_prefix(prop):
    query_obj = DBSession.query(Property.prefix).filter(
        Property.property == prop
    ).first()
    if query_obj.prefix is None:
        return prop
    else:
        return query_obj.prefix+prop


# get the list of searchable study properties
# v3 list pruned down to only those implemented in v3
def get_study_property_list():
    properties = []
    query_obj = DBSession.query(Property.property).filter(
        Property.type=='study'
    ).all()
    for row in query_obj:
        properties.append(row.property)
    return properties

# return the query object without any filtering
# (query not yet executed)
def get_study_query_object(verbose):
    query_obj = None
    if (verbose):
        # Get the study parameters returned by the method when verbose
        # Decorated properties have '^' at the start, becuase that is how they
        # appear in the JSON column
        labels = get_study_parameters(decorated=False)
        clist = get_study_parameters(decorated=True)
        # assigning labels like this makes it easy to build the response json
        # but can't directly access any particular item via the label,
        # i.e result.ot:studyId because of ':' in label
        query_obj = DBSession.query(
            Study.id.label('ot:studyId'),
            Study.data[(clist[0])].label(labels[0]),
            Study.data[(clist[1])].label(labels[1]),
            Study.data[(clist[2])].label(labels[2]),
            Study.data[(clist[3])].label(labels[3]),
            Study.data[(clist[4])].label(labels[4]),
            Study.data[(clist[5])].label(labels[5]),
            Study.data[(clist[6])].label(labels[6]),
            Study.data[(clist[7])].label(labels[7]),
        )
    else:
        query_obj = DBSession.query(Study.id.label('ot:studyId'))
    return query_obj

# find studies by curators; uses Study-Curator association table
def query_studies_by_curator(query_obj,property_value):
    filtered = query_obj.filter(
        Study.curators.any(name=property_value)
        )
    return filtered

# looking for a value in a list, e.g. ot:tag
def query_by_tag(query_obj,property_value):
    property_type = '^ot:tag'
    filtered = query_obj.filter(
        Study.data.contains({property_type:[property_value]})
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

# find studies in cases where the property_value is an int
def query_studies_with_int_values(query_obj,property_type,property_value):
    property_type = get_prop_with_prefix(property_type)
    filtered = query_obj.filter(
        Study.data[
            (property_type)
        ].astext.cast(sqlalchemy.Integer) == property_value
        )
    return filtered

# filter query to return only studies that match property_type and
# property_value
def query_studies(verbose,property_type,property_value):
    _LOG.debug("querying studies by {p} : {v}".format(p=property_type,v=property_value))

    # get the base (unfiltered) query object
    query_obj = get_study_query_object(verbose)
    filtered = None

    # for studyId, use id column rather than ^ot:studyId json property
    if property_type == "ot:studyId":
        filtered = query_obj.filter(Study.id == property_value)

    # curator uses study-curator association table
    elif property_type == "ot:curatorName":
        filtered = query_studies_by_curator(query_obj,property_value)

    # year and focal clade are in json, need to cast an int to string
    elif property_type == "ot:studyYear" or property_type == "ot:focalClade":
        filtered = query_studies_with_int_values(query_obj,property_type,property_value)
    #     property_type = get_prop_with_prefix(property_type)
    #     str_value = str(property_value)
    #     filtered = query_obj.filter(
    #         Study.data[
    #             (property_type)
    #         ].astext == str_value
    #         )

    # value of ot:studyPublication and ot:dataDeposit
    # is a dict with key '@href'
    elif property_type == "ot:studyPublication" or property_type == "ot:dataDeposit":
        property_type = get_prop_with_prefix(property_type)
        filtered = query_obj.filter(
            Study.data[
                (property_type,'@href')
            ].astext == property_value
            )

    elif property_type == "ot:studyPublicationReference" or property_type == "ot:comment":
        filtered = query_fulltext(query_obj,property_type,property_value)

    elif property_type == "treebaseId":
        filtered = query_obj.filter(Study.treebase_id == property_value)

    # tag is a list
    elif property_type == "ot:tag":
        filtered = query_by_tag(query_obj,property_value)

    # all other property types are strings contained in json
    else:
        property_type = get_prop_with_prefix(property_type)
        filtered = query_obj.filter(
            Study.data[
                (property_type)
            ].astext == property_value
            )

    # get results as dict, where keys are the labels set in
    # get_study_query_object
    resultlist = []
    try:
        for row in filtered.all():
            item = {}
            clean_dict_values(row._asdict(), item)
            resultlist.append(item)
        return resultlist
    except ProgrammingError as e:
        _LOG.exception('exception in dict creation'.format(e))
        raise HTTPBadRequest()
