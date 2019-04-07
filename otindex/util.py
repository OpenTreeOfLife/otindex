
def clean_dict_values(inputdict, output):
    for k, v in inputdict.items():
        if v is not None:
            if isinstance(v, dict) and '@href' in v:
                output[k] = v['@href']
            else:
                output[k] = v



def get_study_properties(decorated=False):
    properties = [
            "ot:studyPublicationReference","ot:curatorName",
            "ot:studyYear","ot:focalClade","ot:focalCladeOTTTaxonName",
            "ot:dataDeposit","ot:studyPublication","ot:tag"
            ]
    dec_properties = ["^{}".format(prop) for prop in properties]
    if decorated:
        return dec_properties
    else:
        return properties


def get_tree_properties(decorated=False):
    properties = [
                "ot:treebaseOTUId", "ot:nodeLabelMode", "ot:originalLabel",
                "oti_tree_id",  "ot:inferenceMethod",
                "ot:tag", "ot:treebaseTreeId", "ot:comment", "ot:branchLengthDescription",
                "ot:treeModified","ot:branchLengthTimeUnits",
                "ot:branchLengthMode", "ot:treeLastEdited", "ot:nodeLabelDescription" 
                ]
    # Pulled these , non-JSON properties out
    #"ot:ottTaxonName",  "ot:ottId",  "ot:studyId", 
    dec_properties = ["^{}".format(prop) for prop in properties]
    if decorated:
        return dec_properties
    else:
        return properties
