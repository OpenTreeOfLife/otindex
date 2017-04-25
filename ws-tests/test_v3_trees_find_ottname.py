#!/usr/bin/env python
import sys, os
from opentreetesting import test_http_json_method, config
DOMAIN = config('host', 'apihost')
CONTROLLER = DOMAIN + '/v3/studies'
SUBMIT_URI = CONTROLLER + '/find_trees'

# various tests for OTT taxon names

################################################
# find tree based on a given OTT ID
p = {'verbose': False,
     'property': 'ot:ottTaxonName',
     'value': 'Gaviiformes'}
r = test_http_json_method(SUBMIT_URI,
                          'POST',
                          data=p,
                          expected_status=200,
                          return_bool_data=True)

#structure of r is (true/false,json-results,true/false)
assert r[0] is True
json_result = r[1]
assert len(json_result) > 0

# should return only study_Id, treeID
top_level_key = json_result.keys()[0]
assert top_level_key == 'matched_studies'
assert len(json_result[top_level_key]) > 0

# test with bad name
################################################
p = {'verbose': False,
     'property': 'ot:ottTaxonName',
     'value': 'bad_name'}
r = test_http_json_method(SUBMIT_URI,
                          'POST',
                          data=p,
                          expected_status=404,
                          return_bool_data=True)

#structure of r is (true/false,json-results,true/false)
assert r[0] is True

# test with homonym
p = {'verbose': False,
     'property': 'ot:ottTaxonName',
     'value': 'Erica'}
r = test_http_json_method(SUBMIT_URI,
                          'POST',
                          data=p,
                          expected_status=404,
                          return_bool_data=True)

#structure of r is (true/false,json-results,true/false)
assert r[0] is True
