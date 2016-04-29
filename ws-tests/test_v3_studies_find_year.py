#!/usr/bin/env python
import sys, os
from opentreetesting import test_http_json_method, config
DOMAIN = config('host', 'apihost')
CONTROLLER = DOMAIN + '/v3/studies'
SUBMIT_URI = CONTROLLER + '/find_studies'

################################################
# find study matching year, using verbose = False
p = {'verbose': False,
     'property': 'ot:studyYear',
     'value': '2015'}
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

################################################
# same, but also test that year as int works
p = {'verbose': False,
     'property': 'ot:studyYear',
     'value': 2015}
r = test_http_json_method(SUBMIT_URI,
                          'POST',
                          data=p,
                          expected_status=200,
                          return_bool_data=True)

#structure of r is (true/false,json-results,true/false)
assert r[0] is True
json_result = r[1]
assert len(json_result) > 0

# should return only study_Id for a single study
top_level_key = json_result.keys()[0]
print 'top key: ',top_level_key
assert top_level_key == 'matched_studies'
assert json_result[top_level_key][0].keys() == ['ot:studyId']
