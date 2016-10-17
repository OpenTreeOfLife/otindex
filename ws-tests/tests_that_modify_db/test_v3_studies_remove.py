#!/usr/bin/env python

# test update study by checking db properties before and after update

import sys, os
from opentreetesting import test_http_json_method, config
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
print "studies, trees: {s}, {t}".format(
    s=nstudies_start,
    t=ntrees_start,
)

# remove a study
# study_id = 'ot_688'
p = ["https://github.com/OpenTreeOfLife/phylesystem-1/blob/master/study/ot_88/ot_688/ot_688.json"]
CONTROLLER = DOMAIN + '/v3'
SUBMIT_URI = CONTROLLER + '/remove_studies'
r = test_http_json_method(SUBMIT_URI,
                          'POST',
                          data=p,
                          expected_status=200,
                          return_bool_data=True)

assert r[0] is True

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
print "studies, trees: {s}, {t}".format(
    s=nstudies_end,
    t=ntrees_end,
)

assert nstudies_end < nstudies_start
assert ntrees_end < ntrees_start