##################################################
# views.py: All methods directly implement routes
# defined in __init__.py.
##################################################

from pyramid.response import Response
from pyramid.view import view_config, exception_view_config
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

_LOG = logging.getLogger(__name__)


@exception_view_config(HTTPBadRequest, renderer='json')
# Exception 400 bad request
def exc_view_bad_request(message, request):
    body = {
        "message": str(message),
        "status": 400
    }
    request.response.status = 400
    return body

@exception_view_config(HTTPNotFound, renderer='json')
# Exception 400 bad request
def exc_view_bad_request(message, request):
    body = {
        "message": str(message),
        "status": 404
    }
    request.response.status = 404
    return body

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
    _LOG.debug('request headers are: {h}'.format(h=request.headers))
    _LOG.debug('truncated request.response is: {r}'.format(r=request.response)[:1000])
#    add_cors(request)
#    _LOG.debug('request.response is: {r}'.format(r=request.response))
    if (request.body):
        _LOG.debug('find_studies request.body is {b}'.format(b=request.body))
        try:
            payload = request.json_body
            _LOG.debug('find_studies payload is {p}'.format(p=payload))
        except:
            payload = {'verbose':True}
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
            _LOG.debug('property in payload')
            if 'value' in payload:
                property_type = payload['property']
                property_value = payload['value']
                # is this a valid property?
                study_properties = qs.get_study_property_list()
                if property_type not in study_properties:
                    _msg="Study property {p} is unknown".format(p=property_type)
                    _LOG.exception("HTTPBadRequest: {m}".format(m=_msg))
                    raise HTTPBadRequest(body=_msg)

            else:
                # no value for property
                _msg = "No value given for property {p}".format(p=property_type)
                _LOG.exception("HTTPBadRequest: {m}".format(m=_msg))
                raise HTTPBadRequest(body=_msg)
    else:
        _LOG.debug('find_studies with no parameters')
    # query time!
    if (property_type is None):
        _LOG.debug('property_type is None')
        resultlist = qs.get_all_studies(verbose)
    else:
        _LOG.debug('views: query_studies with  {v},{pt},{pv}'.format(v=verbose,pt=property_type,pv=property_value))
        resultlist = qs.query_studies(verbose,property_type,property_value)
    resultdict = { "matched_studies" : resultlist}
    _LOG.debug("the truncated result dict is {d}".format(d=str(resultdict)[:1000]))
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
                    _msg="Tree property {p} is unknown".format(p=property_type)
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
                _LOG.debug(str(e))
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


@view_config(route_name='parse_phylesystem_webhook', renderer='json', request_method='POST')
def parse_phylesystem_webhook(request):
    if (request.body):
        payload = request.json_body

    # get list of study ids to be added / modified / removed
    try:
        # how we nudge the index depends on which studies are new, changed, or deleted
        added_study_ids = [ ]
        modified_study_ids = [ ]
        removed_study_ids = [ ]
        # TODO: Should any of these lists override another? maybe use commit timestamps to "trump" based on later operations?
        for commit in payload['commits']:
            _harvest_study_ids_from_paths( commit['added'], added_study_ids )
            _harvest_study_ids_from_paths( commit['modified'], modified_study_ids )
            _harvest_study_ids_from_paths( commit['removed'], removed_study_ids )

        # add and update treated the same, so merge
        # also "flatten" each list to remove duplicates
        add_or_update_ids = added_study_ids + modified_study_ids
        add_or_update_ids = list(set(add_or_update_ids))
        remove_ids = list(set(removed_study_ids))

    except:
        raise HTTP(400,json.dumps({"error":1, "description":"malformed GitHub payload"}))

    if payload['repository']['url'] != opentree_docstore_url:
        raise HTTP(400,json.dumps({"error":1, "description":"wrong repo for this API instance"}))

    
    msg = ''
    if len(add_or_update_ids) > 0:
        failed_studies = []
        updated_studies = []
        for study in add_or_update_ids:
            try:
                aus.update_study(study)
            except Exception as e:
                failed_studies.append(study)
                _LOG.debug('failed to update study {s}'.format(s=study))
                _LOG.debug(str(e))
            else:
                updated_studies.append(study)
                _LOG.debug('updated study {s}'.format(s=study))
        results = {
            "failed_studies" : failed_studies,
            "updated_studies" : updated_studies
            }
        return results
    else:
        _msg="add_or_update failure"
        raise HTTPBadRequest(body=_msg)
    if len(remove_ids) > 0:
        for study in remove_ids:
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

    # Clear any cached study lists (both verbose and non-verbose)
    api_utils.clear_matching_cache_keys(".*find_studies.*")

    github_webhook_url = "%s/settings/hooks" % opentree_docstore_url
    full_msg = """This URL should be called by a webhook set in the docstore repo:
                <br /><br />
                <a href="%s">%s</a><br />
                <pre>%s</pre>
                """ % (github_webhook_url, github_webhook_url, msg,)
    if msg == '':
        return full_msg
    else:
        raise HTTP(500, full_msg)






# def parse_amendment_webhook(request):
#     """"Support method to update taxon index (taxomachine) in response to GitHub webhooks

#     This examines the JSON payload of a GitHub webhook to see which taxa have
#     been added, modified, or removed. Then it calls the appropriate index service to
#     (re)index these taxa, or to delete a taxon's information if it was deleted in
#     an amendment.

#     TODO: Clear any cached taxon list.

#     N.B. This depends on a GitHub webhook on the taxonomic-amendments docstore!
#     """

#     amendments_repo_url = _read_from_local_config(request, "apis", "amendments_repo_url")
#     payload = request.vars
#     if payload['repository']['url'] != amendments_repo_url:
#         raise HTTP(400,json.dumps({"error":1, "description":"wrong repo for this API instance"}))

#     msg = ''
#     try:
#         # how we nudge the index depends on which taxa are new, changed, or deleted
#         added_ott_ids = [ ]
#         modified_ott_ids = [ ]
#         removed_ott_ids = [ ]
#         # TODO: Should any of these lists override another? maybe use commit timestamps to "trump" based on later operations?
#         for commit in payload['commits']:
#             _harvest_ott_ids_from_paths( commit['added'], added_ott_ids )
#             _harvest_ott_ids_from_paths( commit['modified'], modified_ott_ids )
#             _harvest_ott_ids_from_paths( commit['removed'], removed_ott_ids )
#         # "flatten" each list to remove duplicates
#         added_ott_ids = list(set(added_ott_ids))
#         modified_ott_ids = list(set(modified_ott_ids))
#         removed_ott_ids = list(set(removed_ott_ids))
#     except:
#         raise HTTP(400,json.dumps({"error":1, "description":"malformed GitHub payload"}))

#     # build a working URL, gather amendment body, and nudge the index!
#     amendments_api_base_url = api_utils.get_amendments_api_base_url(request)

#     if len(added_ott_ids) > 0:
#         nudge_url = "{b}v3/taxonomy/process_additions".format(b=amendments_api_base_url)

#         for ott_id in added_ott_ids:
#             # fetch the JSON body of each new amendment and submit it for indexing
#             fetch_url = "{b}v3/amendment/{i}".format(b=amendments_api_base_url, i=ott_id)
#             fetch_response = None
#             req = urllib2.Request(
#                 url=fetch_url
#             )
#             try:
#                 fetch_response = urllib2.urlopen(req).read()
#                 # strip away metadata (version history, etc.)
#                 amendment_blob = json.loads( fetch_response ).get('data')
#             except Exception, e:
#                 # bail and report the error in webhook response
#                 exc_type, exc_value, exc_traceback = sys.exc_info()
#                 msg += """fetch of amendment failed!'
#     fetch_url: %s
#     fetch_response: %s
#     ott_id: %s
#     %s""" % (fetch_url, fetch_response, ott_id, traceback.format_exception(exc_type, exc_value, exc_traceback),)
#                 break

#             # Extra weirdness required here, as neo4j needs an encoded *string*
#             # of the amendment JSON, within a second JSON wrapper :-/
#             POST_blob = {"addition_document": json.dumps(amendment_blob) }
#             POST_string = json.dumps(POST_blob)
#             nudge_response = None
#             req = urllib2.Request(
#                 url=nudge_url,
#                 data=POST_string,
#                 headers={"Content-Type": "application/json"}
#             )
#             try:
#                 # N.B. we don't expect anything interesting here, probably just an empty dict
#                 nudge_response = urllib2.urlopen(req).read()
#             except Exception, e:
#                 # report the error in webhook response
#                 exc_type, exc_value, exc_traceback = sys.exc_info()
#                 msg += """index amendments failed!'
#     nudge_url: %s
#     POST_data: %s
#     fetch_response: %s
#     nudge_response: %s
#     added_ott_ids: %s
#     %s""" % (nudge_url, POST_data, fetch_response, nudge_response, added_ott_ids, traceback.format_exception(exc_type, exc_value, exc_traceback),)

#     # LATER: add handlers for modified and removed taxa?
#     if len(modified_ott_ids) > 0:
#         raise HTTP(400,json.dumps({
#             "error":1,
#             "description":"We don't currently re-index modified taxa!"}))
#     if len(removed_ott_ids) > 0:
#         raise HTTP(400,json.dumps({
#             "error":1,
#             "description":"We don't currently re-index removed taxa!"}))

#     # N.B. If we had any cached amendment results, we'd clear them now
#     #api_utils.clear_matching_cache_keys(...)

#     github_webhook_url = "%s/settings/hooks" % amendments_repo_url
#     full_msg = """This URL should be called by a webhook set in the amendments repo:
#                     <br /><br />
#                     <a href="%s">%s</a><br />
#                     <pre>%s</pre>
#         """ % (github_webhook_url, github_webhook_url, msg,)
#     if msg == '':
#         return full_msg
#     else:
#         raise HTTP(500, full_msg)

# def _read_from_local_config(request, section_name, key_name):
#     app_name = request.application
#     conf = SafeConfigParser(allow_no_value=True)
#     if os.path.isfile("%s/applications/%s/private/localconfig" % (os.path.abspath('.'), app_name,)):
#         conf.read("%s/applications/%s/private/localconfig" % (os.path.abspath('.'), app_name,))
#     else:
#         conf.read("%s/applications/%s/private/config" % (os.path.abspath('.'), app_name,))
#     return conf.get(section_name, key_name)

# def _harvest_study_ids_from_paths( path_list, target_array ):
#     for path in path_list:
#         path_parts = path.split('/')
#         if path_parts[0] == "study":
#             # skip any intermediate directories in docstore repo
#             study_id = path_parts[ len(path_parts) - 2 ]
#             target_array.append(study_id)

# def _harvest_ott_ids_from_paths( path_list, target_array ):
#     for path in path_list:
#         path_parts = path.split('/')
#         # ignore changes to counter file, other directories, etc.
#         if path_parts[0] == "amendments":
#             # skip intermediate directories in docstore repo
#             amendment_file_name = path_parts.pop()
#             ott_id = amendment_file_name[:-5]
#             target_array.append(ott_id)