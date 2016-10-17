
# tests the new 'about' method
import sys, os
from opentreetesting import test_http_json_method, config
DOMAIN = config('host', 'apihost')
CONTROLLER = DOMAIN + '/v3/studies'
SUBMIT_URI = CONTROLLER + '/about'
r = test_http_json_method(SUBMIT_URI,
                          'GET',
                          expected_status=200,
                          return_bool_data=True)
assert r[0] is True
k = r[1].keys()
assert 'data_store_url' in k
assert 'number_studies' in k
assert 'number_trees' in k
assert 'number_studies' in k
assert 'number_otus' in k
