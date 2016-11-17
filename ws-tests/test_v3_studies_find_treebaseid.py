#!/usr/bin/env python
import sys, os
from opentreetesting import test_http_json_method, config
DOMAIN = config('host', 'apihost')
CONTROLLER = DOMAIN + '/v3/studies'
SUBMIT_URI = CONTROLLER + '/find_studies'

################################################
# find trees for given studyId, using verbose = True
p = {'verbose': False,
     'property': 'treebaseId',
     'value': 'S10963'}
r = test_http_json_method(SUBMIT_URI,
                          'POST',
                          data=p,
                          expected_status=200,
                          return_bool_data=True)

#structure of r is (true/false,json-results,true/false)
assert r[0] is True
json_result = r[1]
#print json_result
# should return only study_Id
top_level_key = json_result.keys()[0]
assert top_level_key == 'matched_studies'
