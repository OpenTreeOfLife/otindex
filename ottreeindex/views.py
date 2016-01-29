from pyramid.response import Response
from pyramid.view import view_config
from pyramid.url import route_url

from pyramid.httpexceptions import (
    HTTPNotFound,
    HTTPBadRequest,
    )

from sqlalchemy.exc import DBAPIError

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
        "source_url": "https://github.com/kcranston/ottreeindex/",
    }

@view_config(route_name='find_studies', renderer='json', request_method='GET')
def find_studies(request):
    # payload should contain some number of parameter=value pairs
    # valid parameters are 'exact', 'verbose' and 'p'
    # where p = (a valid study property)
    payload = request.params
    resultlist = []
    # set defaults
    exact = False
    verbose = False
    if 'exact' in payload:
        exact = payload['exact']
    if 'verbose' in payload:
        verbose = payload['verbose']
    if verbose is True:
        # return data about studies
        for id in DBSession.query(Study.id):
            resultlist.append({"ot:studyId" : id})
    else:
        # return only study IDs
        for id in DBSession.query(Study.id):
            resultlist.append({"ot:studyId" : id})
    resultdict = { "matched_studies" : resultlist}
    return resultdict

@view_config(route_name='find_trees', renderer='json', request_method='GET')
def find_trees(request):
    payload = request.params
    result_json = {}
    return result_json

@view_config(route_name='properties', renderer='json', request_method='GET')
def properties(request):
    # no parameters for this method, simply returns list of tree and
    # study properties
    # junk data for now
    tree_props= [
        "ot:treebaseOTUId", "ot:nodeLabelMode",
        "ot:originalLabel", "oti_tree_id",
        "ot:ottTaxonName", "ot:inferenceMethod",
        "ot:tag", "ot:treebaseTreeId",
        ]
    study_props = [
        "ot:studyModified", "ot:focalClade",
        "ot:focalCladeOTTTaxonName", "ot:focalCladeOTTId",
        "ot:studyPublication", "ot:studyLastEditor",
        "ot:tag", "ot:focalCladeTaxonName",
    ]
    result_json = {
        "tree_properties" : tree_props,
        "study_properties" : study_props
        }
    return result_json

@view_config(route_name='add_update_studies', renderer='json', request_method='POST')
def add_update_studies(request):
    payload = request.params

@view_config(route_name='remove_studies', renderer='json', request_method='POST')
def remove_studies(request):
    payload = request.params
    # delete studies & trees listed in payload
    # also delete otus only used in these studies
