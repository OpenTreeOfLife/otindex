#!/usr/bin/env python

# tests the find_studies method without parameters
# should return study IDs for all studies
import sys, os
from opentreetesting import test_http_json_method, config
DOMAIN = config('host', 'apihost')
CONTROLLER = DOMAIN + '/v3/studies'
SUBMIT_URI = CONTROLLER + '/find_studies'
r = test_http_json_method(SUBMIT_URI,
                          'POST',
                          expected_status=200,
                          return_bool_data=True)
assert r[0] is True
assert len(r[1]) > 0
assert r[1][0].keys() == ['ot:studyId']
