# Generates the three taxonomy files:
#   ott.csv: taxonomy
#   synonyms.csv: synonyms
#   tree_otu_assoc.csv: association between otus and trees

# Assumes that phylesystem has already been loaded (tree table)

import datetime as dt
import argparse
import psycopg2 as psy
import csv, io, os

# other database functions
from . import setup_db

# peyotl functions for handling the taxonomy
from peyotl.api.phylesystem_api import PhylesystemAPI
from peyotl.phylesystem.phylesystem_umbrella import Phylesystem
from peyotl import gen_otu_dict, iter_node
from peyotl.manip import iter_trees
from peyotl import get_logger
import peyotl.ott as ott

_LOG = get_logger()

def create_phylesystem_obj():
    # create connection to local phylesystem
    phylesystem_api_wrapper = PhylesystemAPI(get_from='local')
    phylesystem = phylesystem_api_wrapper.phylesystem_obj
    return phylesystem

# return the (internal) integer tree id from the phylesystem study and tree id
def getTreeID(cursor,study_id,tree_id):
    sqlstring = ('SELECT id FROM {tablename} '
        'WHERE study_id=%s and tree_id=%s;'
        .format(tablename='tree')
        )
    data = (study_id,tree_id)
    _LOG.debug('SQL: {p}'.format(p=cursor.mogrify(sqlstring,(data))))
    cursor.execute(sqlstring,data)
    result = cursor.fetchone()
    if result is not None:
        treeid = result[0]
        return treeid
    else: #todo can fail if trees were added since db was built
        raise LookupError('study {s}, tree {t}'
            ' not found'.format(s=study_id,t=tree_id))

# used to get path to parents for tree association to higher taxa
def parent_closure(ottIDs,taxonomy):
    newids = set()
    for ottID in ottIDs:
        nextid = ottID
        while True:
            newids.add(nextid)
            if taxonomy == None: break
            nextid = taxonomy.ott_id2par_ott_id.get(nextid)
            if nextid == None:
                break
    return newids

# iterates over trees in phylesystem, collecting association between trees and
# otus (including higher taxa)
def prepare_otu_tree_file(connection,cursor,phy,taxonomy,nstudies=None):
    tree_otu_filename = "tree_otu_assoc.csv"

    skipped_otus = set()

    with open(tree_otu_filename, 'w') as g:
        gwriter = csv.writer(g)
        gwriter.writerow(('ott_id','tree_id'))
        # datafile format is 'ott_id \t tree_id' where treeid is not
        # the treeid (string) in the nexson, but the treeid (int) from
        # the database for faster indexing
        counter = 0
        for study_id, studyobj in phy.iter_study_objs():
            otu_dict = gen_otu_dict(studyobj)
            # iterate over the OTUs in the study, collecting the mapped
            # ones (oid to ott_id mapping held at the study level)
            mapped_otus = {}
            for oid, o in list(otu_dict.items()):
                ottID = o.get('^ot:ottId')
                if ottID is not None:
                    mapped_otus[oid]=ottID

            # iterate over the trees in the study, collecting
            # tree/otu associations (including lineage)
            for trees_group_id, tree_id, tree in iter_trees(studyobj):
                # the unique identifier in the tree table is an auto-incrementing
                # int, not the tree_id in the nexson, which is not unique
                _LOG.debug('{i} getting otus for tree  {t} for study {s}'.format(
                           i=counter,
                           s=study_id,
                           t=tree_id)
                           )
                tree_int_id = getTreeID(cursor,study_id,tree_id) #todo can fail if trees were added since db was built
                ottIDs = set()     # ott ids for this tree
                for node_id, node in iter_node(tree):
                    oid = node.get('@otu')
                    # no @otu property on internal nodes
                    if oid is not None:
                        #ottID = mapped_otus[oid]
                        if oid in mapped_otus:
                            ottID = mapped_otus[oid]
                            # check that this exists in the taxonomy
                            # (it might not, if the ID has been deprecated)
                            if taxonomy.ott_id_to_names.get(ottID):
                                ottIDs.add(ottID)
                            else:
                                skipped_otus.add(ottID)
                ottIDs = parent_closure(ottIDs,taxonomy)
                for ottID in ottIDs:
                    gwriter.writerow((ottID,tree_int_id))
            counter+=1
            if (counter%500 == 0):
                print((" prepared",counter,"studies"))
            if (nstudies and counter>=nstudies):
                g.close()
                break
    n_skipped = len(skipped_otus)
    if n_skipped>0:
        _LOG.debug('Skipped {s} mapped OTUs not in OTT'.format(s=n_skipped))

# outputs the taxonomy and synonym csv files
def prepare_taxonomy_files(taxonomy):
    # get dictionary of ottids:ottnames, noting that the names can be strings
    # or tuples, e.g. (canonical name,synonym,synonym)
    print("Loading taxonomy names and parents into memory")
    ott_names = taxonomy.ott_id_to_names
    # dictionary of ottid:parent_ottid
    ott_parents = taxonomy.ott_id2par_ott_id
    print((" exporting {t} names".format(
        t=len(ott_names),
    )))
    ott_filename = "ott.csv"
    synonym_filename = "synonyms.csv"
    # this creates the primary_key column for the synonym table
    # should really modify the copy method to take a column list
    synonym_id = 1
    counter = 0
    print("Exporting taxon information")
    try:
        with open(ott_filename,'w') as of, open(synonym_filename,'w') as sf:
            ofwriter = csv.writer(of)
            sfwriter = csv.writer(sf)
            ofwriter.writerow(('id','name','parent'))
            sfwriter.writerow(('id','ott_id','synonym'))

            for ott_id in ott_names:
                name = ott_names[ott_id]
                synonyms=[]
                # if names is a tuple, then the first element is the unique name
                # and the others are synonyms
                if (isinstance(name,tuple)):
                    synonyms = name[1:]
                    name = name[0]
                parent_id = ott_parents[ott_id]
                # if this is the root, use -1 as the parent
                if parent_id == None:
                    parent_id = -1
                ofwriter.writerow((ott_id,name.encode('utf-8'),parent_id))

                # print synonym data
                for s in synonyms:
                    sfwriter.writerow((synonym_id,ott_id,s.encode('utf-8')))
                    synonym_id+=1

                counter+=1
                if (counter%500000 == 0):
                    print((" exported",counter,"taxa"))
        of.close()
        sf.close()
    except IOError as xxx_todo_changeme:
        (errno,strerror) = xxx_todo_changeme.args
        print(("I/O error({0}): {1}".format(errno, strerror)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='load generate taxonomy files for  postgres')
    parser.add_argument('configfile',
        help='path to the development.ini file'
        )

    parser.add_argument('-n',
        dest='nstudies',
        type=int,
        help='generate tree-otu file for only n studies; if absent, load all studies'
        )
    args = parser.parse_args()

    # read config variables
    config_obj = setup_db.read_config(args.configfile)

    # load taxonomy; location from peyotl config
    taxonomy = ott.OTT()
    print(("Using OTT version {v}".format(v=taxonomy.version)))

    connection, cursor = setup_db.connect(config_obj)
    phy = create_phylesystem_obj()

    try:
        starttime = dt.datetime.now()
        print('Generating taxonomy and synonyms files')
        prepare_taxonomy_files(taxonomy)

        print('Preparing tree - otu association file')
        prepare_otu_tree_file(connection,cursor,phy,taxonomy,args.nstudies)

        endtime = dt.datetime.now()
        print(("OTT file generation time: ",endtime - starttime))
    except psy.Error as e:
        print((e.pgerror))
