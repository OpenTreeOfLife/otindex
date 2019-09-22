
def clean_dict_values(inputdict, output):
    for k, v in inputdict.items():
        if v is not None:
            if isinstance(v, dict) and '@href' in v:
                output[k] = v['@href']
            else:
                output[k] = v


# get the list of study parameters returned when verbose = True
def get_study_parameters(decorated=False):
    properties = [
            "ot:studyPublicationReference","ot:curatorName",
            "ot:studyYear","ot:focalClade","ot:focalCladeOTTTaxonName",
            "ot:dataDeposit","ot:studyPublication","ot:tag", "ot:studyId", "ntrees", "treebaseId"
            ]
    dec_properties = ["^{}".format(prop) for prop in properties]
    if decorated:
        return dec_properties
    else:
        return properties
