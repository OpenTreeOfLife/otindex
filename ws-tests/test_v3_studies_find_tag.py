#!/usr/bin/env python
import sys, os
from opentreetesting import test_http_json_method, config
DOMAIN = config('host', 'apihost')
CONTROLLER = DOMAIN + '/v3/studies'
SUBMIT_URI = CONTROLLER + '/find_studies'

################################################
# find study with given tag, using verbose = False
# study can have multiple tags
p = {'verbose': False,
     'property': 'ot:tag',
     'value': 'cpDNA'}
r = test_http_json_method(SUBMIT_URI,
                          'POST',
                          data=p,
                          expected_status=200,
                          return_bool_data=True)

#structure of r is (true/false,json-results,true/false)
assert r[0] is True
json_result = r[1]
print json_result
assert len(json_result) > 0

# should return only study_Id
top_level_key = json_result.keys()[0]
assert top_level_key == 'matched_studies'
assert json_result[top_level_key][0].keys() == ['ot:studyId']
