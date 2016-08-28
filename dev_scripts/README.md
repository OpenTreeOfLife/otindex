# dev_scripts : development and testing scripts.
# Not part of the otindex package; simply for testing

* `test_delete.py` : testing methods for deleting / adding / updating studies
* `dev_models.py` : replicates `ottreeindex/models.py` for testing
* `jsonb_queries.txt` : not a script, but a list of various postgres jsonb queries for testing from the postgres CLI
* `get_property_value_type.py` : figuring out which nexson properties could be lists; uses peyotl
* `get_study_tree_properties.py` : getting top level study and tree keys from phylesystem; uses peyotl
* `sampleQueries.py` : for testing out sqlalchemy ORM query methods outside of pyramid
