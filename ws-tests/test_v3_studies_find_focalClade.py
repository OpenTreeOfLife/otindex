#!/usr/bin/env python
import sys, os
from opentreetesting import test_http_json_method, config
DOMAIN = config('host', 'apihost')
CONTROLLER = DOMAIN + '/v3/studies'
SUBMIT_URI = CONTROLLER + '/find_studies'

# test methods where casting value to integer
# ot:focalClade

################################################
# find study matching focal clade, using verbose = False
# ott765193 = Anatidae
p = {'verbose': False,
     'property': 'ot:focalClade',
     'value': '765193'}
r = test_http_json_method(SUBMIT_URI,
                          'POST',
                          data=p,
                          expected_status=200,
                          return_bool_data=True)

#structure of r is (true/false,json-results,true/false)
assert r[0] is True
json_result = r[1]
assert len(json_result) > 0

top_level_key = json_result.keys()[0]
assert top_level_key == 'matched_studies'
assert json_result[top_level_key][0].keys() == ['ot:studyId']
