# creates a directory of test nexson files of studies that cover
# a given OTT ID
import requests
import json
import argparse

def getStudyList(ottid):
    # curl -X POST http://api.opentreeoflife.org/v2/studies/find_trees \
    # -H "content-type:application/json" -d \
    # '{"property":"ot:ottTaxonName","value":"Garcinia"}'
    payload = {"property":"ot:ottId","value":ottid}
    header = {"content-type":"application/json"}
    url = "http://api.opentreeoflife.org/v2/studies/find_trees"
    # TODO should check response for HTTP errors
    r = requests.post(url, json=payload, headers=header)
    print r.url
    return r.json()

# TODO: new method, that given the results from the API call, copies each
# file from the local phylesystem repo

# given the result from the API call, save each study as a file
def saveStudy(studyid):
    url = "http://api.opentreeoflife.org/v2/study/"+studyid
    r = requests.get(url)
    filename = studyid+'.json'
    print "writing",studyid,"to file"
    with open(filename, 'w') as fp:
        json.dump(r.json(), fp)

if __name__ == "__main__":
    # get command line arg (ottaxonname)
    parser = argparse.ArgumentParser(description='provide an OTT identifier')
    parser.add_argument('ottid', help='OTT taxon id')
    args = parser.parse_args()

    # get list of studies that cover this taxon
    # verbose=true so all in one big json
    print "getting trees for ottid",args.ottid
    studylist = getStudyList(args.ottid)
    for key,value in studylist.iteritems():
        for item in value:
            studyid=item['ot:studyId']
            saveStudy(studyid)
