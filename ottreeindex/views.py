from pyramid.response import Response
from pyramid.view import view_config
from pyramid.url import route_url

from sqlalchemy.exc import DBAPIError

from .models import (
    DBSession,
    MyModel,
    )

@view_config(route_name='find_studies', renderer='json', request_method='GET')
def find_studies(request):
    # payload should contain some number of parameter=value pairs
    # valid parameters are 'exact', 'verbose' and 'p'
    # where p = (a valid study property)
    payload = request.params
    result_json = {}
    return result_json

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

@view_config(route_name='update_studies', rendered='json', request_method='POST')
def update_studies(request):
    payload = request.params
