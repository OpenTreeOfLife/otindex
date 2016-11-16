#!/usr/bin/env python

# test removal of study by checking db properties before and after update
# re-adds the study afterwards, so no net change to database

import sys, os
from opentreetesting import test_http_json_method, config
DOMAIN = config('host', 'apihost')

###################
# Get results from about method before
CONTROLLER = DOMAIN + '/v3/studies'
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
print "starting studies, tree, otus, curators: {s}, {t}, {o}, {c}".format(
    s=nstudies_start,
    t=ntrees_start,
    o=notus_start,
    c=ncurators_start
)

############################
# 1. remove a study
# If you change the study number, pick a study that exists in both
# development and production phylesystems
p = { 'studies' : [ "pg_100" ] }
SUBMIT_URI = CONTROLLER + '/remove'
r = test_http_json_method(SUBMIT_URI,
                          'POST',
                          data=p,
                          expected_status=200,
                          return_bool_data=True)

assert r[0] is True
assert len(r[1]['failed_studies']) == 0

############################
# 2. get results from about method after
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
print "after delete studies, tree, otus, curators: {s}, {t}, {o}, {c}".format(
    s=nstudies_end,
    t=ntrees_end,
    o=notus_end,
    c=ncurators_end
)

assert nstudies_end < nstudies_start
assert ntrees_end < ntrees_start

############################
# 3. re-add the study and check again
SUBMIT_URI = CONTROLLER + '/add_update'
r = test_http_json_method(SUBMIT_URI,
                          'POST',
                          data=p,
                          expected_status=200,
                          return_bool_data=True)

assert r[0] is True
assert len(r[1]['failed_studies']) == 0

############################
# 4. check about method after add / update
CONTROLLER = DOMAIN + '/v3/studies'
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
print "after update studies, tree, otus, curators: {s}, {t}, {o}, {c}".format(
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
