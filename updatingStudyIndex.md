The study index needs to be updated upon changes to the data store (phylesytem)

# OTI procedure

The current (as of August 2016) procedure:

1. User adds / updates / deletes a study using the [curator app](https://tree.opentreeoflife.org/curator)
* The modifications get saved as commits to the [phylesystem-1](https://github.com/OpenTreeOfLife/phylesystem-1) repo
* a GitHub commit hook calls `https://api.opentreeoflife.org/phylesystem/search/nudgeStudyIndexOnUpdates`. The payload includes the details of the commit.
* that call is handled by [phylesystem-api](https://github.com/OpenTreeOfLife/phylesystem-api), specifically the [nudgeStudyIndexOnUpdates method](https://github.com/OpenTreeOfLife/phylesystem-api/blob/56a0f3d531fb3e99a25f2cf4db65aad460d77806/controllers/search.py#L49), which bundles of up the list(s) of added, deleted, and modified study IDs, and calls OTI.
* the OTI method [indexNexsons](https://github.com/OpenTreeOfLife/oti/blob/c4c83101edef0748b72af90e6ef20e76fab5d8eb/src/main/java/org/opentree/oti/plugins/IndexServices.java#L87) handles the call for additions and deletions and [unindexNexsons](https://github.com/OpenTreeOfLife/oti/blob/c4c83101edef0748b72af90e6ef20e76fab5d8eb/src/main/java/org/opentree/oti/plugins/IndexServices.java#L133) handles deletions, both modifying the database as needed

Sample call from phylesystem-api to oti:

`curl -X POST -d '{"urls": ["https://raw.github.com/OpenTreeOfLife/phylesystem/master/study/10/10.json", "https://raw.github.com/OpenTreeOfLife/phylesystem/master/study/9/9.json"]}' -H "Content-type: application/json" http://ec2-54-203-194-13.us-west-2.compute.amazonaws.com/oti/ext/IndexServices/graphdb/indexNexsons`

# Otindex procedure

* Write a generic nudgeIndex method that can handle changes to studies, collections, amendments, or other data types
* The web application will not need to change.
* two possible approaches to triggering:
  * the webhook stays the same, and phylesystem-api calls otindex rather than oti, and the payload specifies that the changes apply to studies (new top-level `studies` key).
  * the webhook calls otindex directly, eliminating phylesystem-api from the loop
* otindex updates the database as needed
  * replace json blob for study and tree
  * update curator and study-curator tables, if needed
  * update otu and tree-otu tables, if needed
