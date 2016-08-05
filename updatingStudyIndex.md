The study index needs to be updated upon changes to the data store (phylesytem)

# OTI procedure

The current (as of August 2016) procedure:

1. User adds / updates / deletes a study using the [curator app](https://tree.opentreeoflife.org/curator)
* The modifications get saved as commits to the [phylesystem-1](https://github.com/OpenTreeOfLife/phylesystem-1) repo
* a GitHub commit hook calls `https://api.opentreeoflife.org/phylesystem/search/nudgeStudyIndexOnUpdates`. The payload includes the details of the commit.
* that call is handled by [phylesystem-api](https://github.com/OpenTreeOfLife/phylesystem-api), specifically the [nudgeStudyIndexOnUpdates method](https://github.com/OpenTreeOfLife/phylesystem-api/blob/56a0f3d531fb3e99a25f2cf4db65aad460d77806/controllers/search.py#L49), which bundles of up the list(s) of added, deleted, and modified study IDs, and calls OTI
* the OTI method [indexNexsons](https://github.com/OpenTreeOfLife/oti/blob/c4c83101edef0748b72af90e6ef20e76fab5d8eb/src/main/java/org/opentree/oti/plugins/IndexServices.java#L87) handles the call, modifying the database as needed

# Ottreeindex procedure

* Write a generic nudgeIndex method that can handle changes to studies, collections, amendments, or other data types
* The web application and webhook will not need to change.
* phylesystem-api calls ottreeindex rather than oti, and the payload specifies that the changes apply to studies (new top-level `studies` key).
* ottreeindex updates the database as needed
