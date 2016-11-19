# start developing methods for adding and updating studies

import requests
import sqlalchemy
import simplejson as json

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    )

from dev_models import (
    Study,
    Tree,
    Curator,
    Otu,
    )

from peyotl.nexson_proxy import NexsonProxy

def study_exists(study_id):
    study = session.query(Study).filter(Study.id==study_id).first()
    if study:
        return True
    else:
        return False

# the cleanest way to do this (although maybe not the fastest) is to
# delete the study, which deletes any orphaned trees, curators, otus and
# removes associations. We then simply re-insert the study. This changes
# the auto-incrementing ids for trees and curators, but we don't expose these
# in any public interface
def update_study_data(session,study_id,nexson):
    # get Study object for this study_id
    study_to_update = session.query(Study).filter(Study.id==study_id).first()

    # delete the study

    # # do we need to update year?
    # study_year = nexson._nexml_el['^ot:studyYear']
    # if not study_to_update.year == study_year:
    #     study_to_update.year = study_year
    #
    # proposedTrees = nexson._nexml_el['^ot:candidateTreeForSynthesis']
    # if proposedTrees is None:
    #     proposedTrees = []
    # # iterate over trees
    # # iterate over otus
    #
    # tree_data = nexson._nexml_el['treesById']
    #
    # # now update the json data field for the study, first removing the
    # # (now redundant) tree data
    # del nexson._nexml_el['treesById']
    # study_to_update.data = json.dumps(nexson._nexml_el)
    #
    # # also need to update otus, curators
    # print session.dirty

def add_new_study(session,study_id,nexson):
    study_year = nexson['^ot:studyYear']
    proposedTrees = nexson['^ot:candidateTreeForSynthesis']
    if proposedTrees is None:
        proposedTrees = []
    nexml = studyobj._nexml_el
    tree_data = nexml['treesById']
    del nexml['treesById']
    new_study = Study(id=study_id,year=study_year,data=nexml)
    # add to session, but don't flush yet. We will do add additions at once
    #DBSession.add(new_study)
    #print tree_data.keys()

def update_study(url,session):
    # get the most recent version of the nexson from github
    request = requests.get(url)
    nexson_blob = request.json()

    # get a peyotl NexsonProxy object, which provides high-level wrappers
    # around the nexson data model
    studyobj = NexsonProxy(nexson=nexson_blob)

    nexml = studyobj._nexml_el
    study_id = nexml['^ot:studyId']
    if study_exists(study_id):
      update_study_data(session,study_id,studyobj)
    else:
      add_new_study(session,study_id,studyobj)

if __name__ == "__main__":
    connection_string = 'postgresql://postgres@localhost/otindex'
    db = sqlalchemy.create_engine(connection_string)
    engine = db.connect()
    meta = sqlalchemy.MetaData(engine)
    SessionFactory = sessionmaker(engine)
    session = SessionFactory()

    # the payload from phylesystem-api contains an array of raw github URLs
    raw_urls = [
        'https://raw.githubusercontent.com/OpenTreeOfLife/phylesystem-1/master/study/ot_07/ot_607/ot_607.json'
        ]
    for url in raw_urls:
        update_study(url,session)
