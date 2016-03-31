from pyramid.response import Response
from pyramid.view import view_config
from pyramid.url import route_url

import simplejson as json

from pyramid.httpexceptions import exception_response

from sqlalchemy.exc import DBAPIError
from sqlalchemy import func

from .models import (
    DBSession,
    Study,
    Tree,
    Curator,
    Otu,
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
# currently implemented: the findall behaviour (returns all studies)
@view_config(route_name="find_studies_v3", renderer='json',request_method="POST")
def find_studies_v3(request):
    # set defaults
    default_json = {"verbose":False,"exact":False}
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
            return exception_response(400)

        if 'verbose' in payload:
            verbose = payload['verbose']

        if 'property' in payload:
            if 'value' in payload:
                property_type = payload['property']
                property_value = payload['value']
                # is this a valid property?
                searchable_properties = get_property_list(3)
                study_properties = searchable_properties['study_properties']
                if property_type not in study_properties:
                    return exception_response(400)
                # ok, now search for studies with this property : value combo

            else:
                # no value for property
                return exception_response(400)

    # query time!

    # return only study IDs
    resultlist = []
    for study in DBSession.query(Study.id):
        item = {}
        item["ot:studyId"]=study.id
        resultlist.append(item)

    # else:
    #     # if no property specified, returning all studies
    #     if verbose:
    #         # return data about studies
    #         for study in DBSession.query(Study.id):
    #             item = {}
    #             item["ot:studyId"]=study.id
    #             item["curator"]="name"
    #             item["verbose"]=verbose
    #             resultlist.append(item)
    #     else:
    #         # return only study IDs
    #         for study in DBSession.query(Study.id):
    #             item = {}
    #             item["ot:studyId"]=study.id
    #             item["verbose"]=verbose
    #             resultlist.append(item)
    #
    resultdict = { "matched_studies" : resultlist}
    return resultdict

def query_studies(verbose=False,property=None,value=None):
    resultlist = []
    fieldlist = []
    if verbose:
         fieldlist = [
            "id","ot:studyPublicationReference","ot:curatorName",
            "ot:studyYear","ot:focalClade","ot:focalCladeOTTTaxonName",
            "ot:dataDeposit","ot:studyPublication"
        ]
    for study in DBSession.query(Study.id):
         item = {}
         # always return studyid
         item["ot:studyId"]=study.id
         # then other optional fields
         #for field in fieldlist:
        #     item[field]=study.field
         resultlist.append(item)
    return resultlist

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
@view_config(route_name='find_trees', renderer='json', request_method="POST")
def find_trees_v3(request):
    payload = request.params
    result_json = {}
    return result_json

# get the list of searchable properties
# currently returns the v3 list only
def get_property_list(version=3):
    tree_props= [
        "ot:treebaseOTUId", "ot:nodeLabelMode", "ot:originalLabel",
        "oti_tree_id", "ot:ottTaxonName", "ot:inferenceMethod", "ot:tag",
        "ot:comment", "ot:treebaseTreeId", "ot:branchLengthDescription",
        "ot:treeModified", "ot:studyId", "ot:branchLengthTimeUnits",
        "ot:ottId", "ot:branchLengthMode", "ot:treeLastEdited",
        "ot:nodeLabelDescription"
        ]
    study_props = [
        "ot:studyModified", "ot:focalClade", "ot:focalCladeOTTTaxonName",
        "ot:focalCladeOTTId", "ot:studyPublication", "ot:studyLastEditor",
        "ot:tag", "ot:focalCladeTaxonName", "ot:comment", "ot:studyLabel",
        "ot:authorContributed", "ot:studyPublicationReference", "ot:studyId",
        "ot:curatorName", "ot:studyYear", "ot:studyUploaded", "ot:dataDeposit"
        ]
    results = {
        "tree_properties" : tree_props,
        "study_properties" : study_props
        }
    return results

# implements the v3 (oti) version of this method
# only change is removal of the (ironically) deprecated is_deprecated property
@view_config(route_name='properties_v3', renderer='json',request_method="POST")
def properties_v3(request):
    version = 3
    results = get_property_list(version)
    return results

@view_config(route_name='add_update_studies_v3', renderer='json', request_method='POST')
def add_update_studies_v3(request):
    payload = request.params

@view_config(route_name='remove_studies_v3', renderer='json', request_method='POST')
def remove_studies_v3(request):
    payload = request.params
    # delete studies & trees listed in payload
    # also delete otus only used in these studies
