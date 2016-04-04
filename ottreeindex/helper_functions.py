# miscellaneous helper functions for views

# get the list of searchable properties
# currently returns the v3 list only
def get_property_list(version=3):
    tree_props= [
        "ot:treebaseOTUId", "ot:nodeLabelMode", "ot:originalLabel",
        "oti_tree_id", "ot:ottTaxonName", "ot:inferenceMethod", "ot:tag",
        "ot:comment", "ot:treebaseTreeId", "ot:branchLengthDescription",
        "ot:treeModified", "ot:studyId", "ot:branchLengthTimeUnits",
        "ot:ottId", "ot:branchLengthMode", "ot:treeLastEdited",
        "ot:nodeLabelDescription"
        ]
    study_props = [
        "ot:studyModified", "ot:focalClade", "ot:focalCladeOTTTaxonName",
        "ot:focalCladeOTTId", "ot:studyPublication", "ot:studyLastEditor",
        "ot:tag", "ot:focalCladeTaxonName", "ot:comment", "ot:studyLabel",
        "ot:authorContributed", "ot:studyPublicationReference", "ot:studyId",
        "ot:curatorName", "ot:studyYear", "ot:studyUploaded", "ot:dataDeposit"
        ]
    results = {
        "tree_properties" : tree_props,
        "study_properties" : study_props
        }
    return results
