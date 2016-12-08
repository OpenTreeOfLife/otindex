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
import logging

from peyotl import get_logger

from otindex import query_study_helpers as qs
from otindex import query_tree_helpers as qt
from otindex import add_update_studies as aus
from otindex.models import (
    DBSession,
    Study,
    Tree,
    Curator,
    Taxonomy,
    Property,
    )

#_LOG = logging.getLogger(__name__)
_LOG = get_logger(__name__)

@view_config(route_name='home', renderer='json')
def index(request):
    return {
        "description": "The Open Tree of Life Phylesystem Index",
        "source_url": "https://github.com/opentreeoflife/otindex/",
    }

# returns information about github repo, number studies,
# number trees, number curators, number OTUs
@view_config(route_name="about",renderer='json')
def about(request):
    nstudies = DBSession.query(Study.id).count()
    ntrees = DBSession.query(Tree.id).count()
    ncurators = DBSession.query(Curator.id).count()
    notus = DBSession.query(Taxonomy.id).count()
    return {
        'data_store_url' : "https://github.com/opentreeoflife/phylesystem/",
        'number_studies' : nstudies,
        'number_trees' : ntrees,
        'number_curators' : ncurators,
        'number_otus' : notus
        }

# finding studies
@view_config(route_name="find_studies", renderer='json',request_method="POST")
def find_studies(request):
    # set defaults
    verbose = False
    exact = False
    property_type = None
    property_value = None
    _LOG.debug('find_studies')

    if (request.body):
        payload = request.json_body
        # check that we only have valid parameters
        valid_parameters = ['verbose','property','value','exact']
        parameters = payload.keys()

        _LOG.debug('find_studies with parameters: {p}'.format(p=parameters))

        extra_params = set(parameters).difference(valid_parameters)
        if len(extra_params) > 0:
            _LOG.debug('found extra parameters: {x}'.format(x=extra_params))
            return HTTPBadRequest()

        if 'verbose' in payload:
            verbose = payload['verbose']

        if 'property' in payload:
            if 'value' in payload:
                property_type = payload['property']
                property_value = payload['value']
                # is this a valid property?
                study_properties = qs.get_study_property_list()
                if property_type not in study_properties:
                    _msg="Property {p} is unknown".format(p=property_type)
                    raise HTTPBadRequest(body=_msg)

            else:
                # no value for property
                _msg = "No value given for property {p}".format(p=property_type)
                raise HTTPBadRequest(body=_msg)

    else:
        _LOG.debug('find_studies with no parameters')

    # query time!
    if (property_type is None):
        resultlist = qs.get_all_studies(verbose)
    else:
        resultlist = qs.query_studies(verbose,property_type,property_value)
    resultdict = { "matched_studies" : resultlist}
    return resultdict

# find_trees method
@view_config(route_name='find_trees', renderer='json', request_method="POST")
def find_trees(request):
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
                tree_properties = qt.get_tree_property_list()
                if property_type not in tree_properties:
                    _msg="Property {p} is unknown".format(p=property_type)
                    raise HTTPBadRequest(body=_msg)

            else:
                _msg="No value given for property {p}".format(p=property_type)
                raise HTTPBadRequest(body=_msg)
    # query time!
    if (property_type is None):
        resultlist = qt.get_all_trees(verbose)
    else:
        resultlist = qt.query_trees(verbose,property_type,property_value)

    resultdict = { "matched_studies" : resultlist}
    return resultdict

@view_config(route_name='properties', renderer='json',request_method="POST")
def properties(request):
    study_props = qs.get_study_property_list()
    tree_props = qt.get_tree_property_list()
    results = {
        "tree_properties" : tree_props,
        "study_properties" : study_props
        }
    return results

# updates one or more studies
# payload can be a list of URLs (oti syntax) or a list of
# study ids
@view_config(route_name='add_update', renderer='json', request_method='POST')
def add_update_studies(request):
    if (request.body):
        payload = request.json_body
        failed_studies = []
        updated_studies = []
        for study in payload['studies']:
            try:
                aus.update_study(study)
            except Exception as e:
                failed_studies.append(study)
                _LOG.debug('failed to update study {s}'.format(s=study))
                _LOG.debug(e.message)
            else:
                updated_studies.append(study)
                _LOG.debug('updated study {s}'.format(s=study))
        results = {
            "failed_studies" : failed_studies,
            "updated_studies" : updated_studies
            }
        return results
    else:
        _msg="No payload provided"
        raise HTTPBadRequest(body=_msg)

# payload can be a list of URLs (oti syntax) or a list of
# study ids
@view_config(route_name='remove', renderer='json', request_method='POST')
def remove_studies(request):
    if (request.body):
        payload = request.json_body
        failed_studies = []
        updated_studies = []
        for study in payload['studies']:
            try:
                aus.remove_study(study)
            except:
                failed_studies.append(study)
                _LOG.debug('failed to remove study {s}'.format(s=study))
            else:
                updated_studies.append(study)
                _LOG.debug('removed study {s}'.format(s=study))
        results = {
            "failed_studies" : failed_studies,
            "updated_studies" : updated_studies
            }
        return results
    else:
        _msg="No payload provided"
        raise HTTPBadRequest(body=_msg)
