
def clean_dict_values(inputdict, output):
    for k, v in inputdict.items():
        if v is not None:
            if isinstance(v, dict) and '@href' in v:
                output[k] = v['@href']
            else:
                output[k] = v

