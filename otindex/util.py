
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
