##################################################
# views.py: All methods directly implement routes
# defined in __init__.py.
##################################################

from pyramid.response import Response
from pyramid.view import view_config
from pyramid.url import route_url
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest

from sqlalchemy.exc import DBAPIError
from sqlalchemy import func

import simplejson as json
import requests

from ottreeindex import query_study_helpers as qs
from ottreeindex import query_tree_helpers as qt
from ottreeindex import add_update_studies as aus
from ottreeindex.models import (
    DBSession,
    Study,
    Tree,
    Curator,
    Taxonomy,
    )

@view_config(route_name='home', renderer='json')
def index(request):
    return {
        "description": "The Open Tree of Life Phylesystem Index",
        "source_url": "https://github.com/opentreeoflife/ottreeindex/",
    }

# returns information about github repo, number studies,
# number trees, number curators, number OTUs
@view_config(route_name="about",renderer='json')
def about(request):
    nstudies = DBSession.query(Study.id).count()
    ntrees = DBSession.query(Tree.id).count()
    ncurators = DBSession.query(Curator.id).count()
    notus = DBSession.query(Otu.id).count()
    return {
        'data_store_url' : "https://github.com/opentreeoflife/phylesystem/",
        'number_studies' : nstudies,
        'number_trees' : ntrees,
        'number_curators' : ncurators,
        'number_otus' : notus
        }

# the v2/v3 (oti equivalent) method for find_studies
@view_config(route_name="find_studies_v3", renderer='json',request_method="POST")
def find_studies_v3(request):
    # set defaults
    verbose = False
    exact = False
    property_type = None
    property_value = None

    if (request.body):
        payload = request.json_body
        # check that we only have valid parameters
        valid_parameters = ['verbose','property','value','exact']
        parameters = payload.keys()
        extra_params = set(parameters).difference(valid_parameters)
        if len(extra_params) > 0:
            return HTTPBadRequest()

        if 'verbose' in payload:
            verbose = payload['verbose']

        if 'property' in payload:
            if 'value' in payload:
                property_type = payload['property']
                property_value = payload['value']
                # is this a valid property?
                study_properties = qs.get_study_property_list(3)
                if property_type not in study_properties:
                    # TODO: return helpful error about bad property
                    return HTTPBadRequest()

            else:
                # no value for property
                # TODO: return helpful error about lacking value for property
                return HTTPBadRequest()

    # query time!
    if (property_type is None):
        resultlist = qs.get_all_studies(verbose)
    else:
        resultlist = qs.query_studies(verbose,property_type,property_value)
    resultdict = { "matched_studies" : resultlist}
    return resultdict

# the v4 method for find_studies
@view_config(route_name='find_studies', renderer='json', request_method='GET')
def find_studies(request):
     # payload should contain some number of parameter=value pairs
     # valid parameters are 'exact', 'verbose' and 'p'
     # where p = (a valid study property)
     payload = request.params
     resultlist = []
#     # set defaults
#     exact = "false"
#     verbose = "false"
#     if 'exact' in payload:
#         exact = payload['exact']
#     if 'verbose' in payload:
#         verbose = payload['verbose']
#
#     if verbose == "true":
#         # return data about studies
#         for id in DBSession.query(Study.id):
#             item = {}
#             item["ot:studyId"]=id
#             item["curator"]="name"
#             item["verbose"]=verbose
#             resultlist.append(item)
#     else:
#         # return only study IDs
#         for id in DBSession.query(Study.id):
#             item = {}
#             item["ot:studyId"]=id
#             item["verbose"]=verbose
#             resultlist.append(item)
     resultdict = { "matched_studies" : resultlist}
     return resultdict

# v3 (oti) find_trees method
@view_config(route_name='find_trees_v3', renderer='json', request_method="POST")
def find_trees_v3(request):
    # set defaults
    verbose = False
    exact = False
    property_type = None
    property_value = None

    if (request.body):
        payload = request.json_body
        # check that we only have valid parameters
        valid_parameters = ['verbose','property','value','exact']
        parameters = payload.keys()
        extra_params = set(parameters).difference(valid_parameters)
        if len(extra_params) > 0:
            return HTTPBadRequest()

        if 'verbose' in payload:
            verbose = payload['verbose']

        if 'property' in payload:
            if 'value' in payload:
                property_type = payload['property']
                property_value = payload['value']
                # is this a valid property?
                tree_properties = qt.get_tree_property_list(3)
                if property_type not in tree_properties:
                    # TODO: return helpful error about bad property
                    return HTTPBadRequest()

            else:
                # no value for property
                # TODO: return helpful error about lacking value for property
                return HTTPBadRequest()
    # query time!
    if (property_type is None):
        resultlist = qt.get_all_trees(verbose)
    else:
        resultlist = qt.query_trees(verbose,property_type,property_value)

    resultdict = { "matched_studies" : resultlist}
    return resultdict

# implements the v3 (oti) version of this method
# only change is removal of the (ironically) deprecated is_deprecated property
@view_config(route_name='properties_v3', renderer='json',request_method="POST")
def properties_v3(request):
    version = 3
    study_props = qs.get_study_property_list(version)
    tree_props = qt.get_tree_property_list(version)
    results = {
        "tree_properties" : tree_props,
        "study_properties" : study_props
        }
    return results

# updates one or more studies
@view_config(route_name='add_update_studies_v3', renderer='json', request_method='POST')
def add_update_studies_v3(request):
    if (request.body):
        payload = request.json_body
        for url in payload:
            aus.update_study(url)
    else:
        # TODO: return helpful error message about requiring at least one URL
        return HTTPBadRequest()

@view_config(route_name='remove_studies_v3', renderer='json', request_method='POST')
def remove_studies_v3(request):
    payload = request.params
    # delete studies & trees listed in payload
    # also delete otus only used in these studies
