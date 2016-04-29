#!/usr/bin/env python
import sys, os
from opentreetesting import test_http_json_method, config
DOMAIN = config('host', 'apihost')
CONTROLLER = DOMAIN + '/v3/studies'
SUBMIT_URI = CONTROLLER + '/find_studies'

################################################
# find study matching DOI, using verbose = False
p = {'verbose': False,
     'property': 'ot:studyPublication',
     'value': 'http://dx.doi.org/10.1600/036364408785679851'}
# DOI was formerly 10.3732/ajb.94.11.1860
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
assert top_level_key == 'matched_studies'
assert len(json_result[top_level_key])==1
assert json_result[top_level_key][0].keys() == ['ot:studyId']

################################################
# repeat test for verbose = True
p = {'verbose': True,
     'property': 'ot:studyPublication',
     'value': 'http://dx.doi.org/10.1600/036364408785679851'}
# DOI was formerly 10.3732/ajb.94.11.1860
r = test_http_json_method(SUBMIT_URI,
                          'POST',
                          data=p,
                          expected_status=200,
                          return_bool_data=True)

assert r[0] is True
json_result = r[1]
assert len(json_result) > 0

# should return several properties for a single study
top_level_key = json_result.keys()[0]
assert top_level_key == 'matched_studies'
assert len(json_result[top_level_key])==1
assert len(json_result[top_level_key][0].keys()) >0
