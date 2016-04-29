#!/usr/bin/env python
import sys, os
from opentreetesting import test_http_json_method, config
DOMAIN = config('host', 'apihost')
CONTROLLER = DOMAIN + '/v3/studies'
SUBMIT_URI = CONTROLLER + '/find_studies'

################################################
# test bad property
p = {'verbose': False,
     'property': 'ot:badProperty',
     'value': '2015'}
r = test_http_json_method(SUBMIT_URI,
                          'POST',
                          data=p,
                          expected_status=400,
                          return_bool_data=False)

#structure of r is (true/false,json-results,true/false)
assert r is True
