#!/usr/bin/env python

# run lots of add / update tests

import sys, os
from opentreetesting import test_http_json_method, config

# peyotl setup
from peyotl.api.phylesystem_api import PhylesystemAPI

DOMAIN = config('host', 'apihost')

# get results from about method before
CONTROLLER = DOMAIN + '/v4/studies'
SUBMIT_URI = CONTROLLER + '/about'
r = test_http_json_method(SUBMIT_URI,
                          'GET',
                          expected_status=200,
                          return_bool_data=True)
assert r[0] is True
nstudies_start = r[1]['number_studies']
ntrees_start = r[1]['number_trees']
notus_start = r[1]['number_otus']
ncurators_start = r[1]['number_curators']
print "START: studies, tree, otus, curators: {s}, {t}, {o}, {c}".format(
    s=nstudies_start,
    t=ntrees_start,
    o=notus_start,
    c=ncurators_start
)

CONTROLLER = DOMAIN + '/v3'
SUBMIT_URI = CONTROLLER + '/add_update_studies'

phylesystem_api_wrapper = PhylesystemAPI(get_from='local')
phy = phylesystem_api_wrapper.phylesystem_obj
counter = 0
start = 10
limit = start+30
for study_id, studyobj in phy.iter_study_objs():
    if counter>start:
        p = [study_id]
        r = test_http_json_method(SUBMIT_URI,
                                  'POST',
                                  data=p,
                                  expected_status=200,
                                  return_bool_data=True)
        assert r[0] is True
        print "updated study",study_id
    counter+=1
    if counter>limit:
        break

# get results from about method after
CONTROLLER = DOMAIN + '/v4/studies'
SUBMIT_URI = CONTROLLER + '/about'
r = test_http_json_method(SUBMIT_URI,
                          'GET',
                          expected_status=200,
                          return_bool_data=True)
assert r[0] is True
nstudies_end = r[1]['number_studies']
ntrees_end = r[1]['number_trees']
notus_end = r[1]['number_otus']
ncurators_end = r[1]['number_curators']
print "END: studies, tree, otus, curators: {s}, {t}, {o}, {c}".format(
    s=nstudies_end,
    t=ntrees_end,
    o=notus_end,
    c=ncurators_end
)

# if study existed, then would be equal, otherwise greater
assert nstudies_end >= nstudies_start
assert ntrees_end >= ntrees_start
assert notus_end >= notus_start
assert ncurators_end >= ncurators_start
