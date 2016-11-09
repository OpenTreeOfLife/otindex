# Collects the OTU - tree relationships across phylesystem
# Prints to file which is then inserted into postgres with COPY
# This is much faster than many inserts

from peyotl.api.phylesystem_api import PhylesystemAPI
from peyotl.phylesystem.phylesystem_umbrella import Phylesystem
from peyotl import gen_otu_dict, iter_node
from peyotl.manip import iter_trees

import setup_db

import psycopg2 as psy
import argparse
import yaml
import csv

import peyotl.ott as ott

def create_phylesystem_obj():
    # create connection to local phylesystem
    phylesystem_api_wrapper = PhylesystemAPI(get_from='local')
    phylesystem = phylesystem_api_wrapper.phylesystem_obj
    return phylesystem

def getTreeID(cursor,study_id,tree_id):
    sqlstring = ('SELECT id FROM {tablename} '
        'WHERE study_id=%s and tree_id=%s;'
        .format(tablename='tree')
        )
    data = (study_id,tree_id)
    #print '  SQL: ',cursor.mogrify(sqlstring,data)
    cursor.execute(sqlstring,data)
    result = cursor.fetchone()
    if result is not None:
        treeid = result[0]
        return treeid
    else:
        raise LookupError('study {s}, tree {t}'
            ' not found'.format(s=study_id,t=tree_id))

def prepare_otu_tree_file(connection,cursor,phy,taxonomy,nstudies=None):
    tree_otu_filename = "tree_otu_assoc.csv"

    #ott_names = taxonomy.ott_id_to_names
    skipped_otus = set()

    with open(tree_otu_filename, 'w') as g:
        gwriter = csv.writer(g)
        # datafile format is 'ottid'\t'treeid' where treeid is not
        # the treeid (string) in the nexson, but the treeid (int) from
        # the database for faster indexing
        counter = 0
        for study_id, n in phy.iter_study_objs():
            otu_dict = gen_otu_dict(n)
            # iterate over the OTUs in the study, collecting the mapped
            # ones (oid to ott_id mapping held at the study level)
            mapped_otus = {}
            for oid, o in otu_dict.items():
                ottID = o.get('^ot:ottId')
                if ottID is not None:
                    mapped_otus[oid]=ottID

            # iterate over the trees in the study, collecting
            # tree/otu associations (including lineage)
            for trees_group_id, tree_id, tree in iter_trees(n):
                # the unique identifier in the tree table is an auto-incrementing
                # int, not the tree_id in the nexson, which is not unique
                tree_int_id = getTreeID(cursor,study_id,tree_id)
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
                    gwriter.writerow((tree_int_id,ottID))

            counter+=1
            if (counter%500 == 0):
                print " prepared",counter,"studies"
            if (nstudies and counter>=nstudies):
                g.close()
                break
    print "skipped {s} mapped OTUs not in OTT".format(s=len(skipped_otus))
    return tree_otu_filename

def parent_closure(ottIDs,taxonomy):
    #newids = {}
    newids = set()
    for ottID in ottIDs:
        nextid = ottID
        while True:
            #newids[nextid] = True
            newids.add(nextid)
            if taxonomy == None: break
            nextid = taxonomy.ott_id2par_ott_id.get(nextid)
            if nextid == None:
                break
    return newids


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='create otu-tree table')
    parser.add_argument('configfile',
        help='path to the config file'
        )
    parser.add_argument('-n',
        dest='nstudies',
        type=int,
        help='load only n studies; if absent, load all studies'
        )
    args = parser.parse_args()

    # read config variables
    config_obj = setup_db.read_config(args.configfile)

    # ott_loc = config_dict['taxonomy']
    # if ott_loc == 'None':
    #     print 'No taxonomy'
    #     taxonomy = None
    # else:
    #     print "Loading taxonomy into memory"
    #     taxonomy = ott.OTT(ott_loc)

    # load taxonomy; location from peyotl config
    taxonomy = ott.OTT()
    connection, cursor = setup_db.connect(config_obj)
    phy = create_phylesystem_obj()
    try:
        TREEOTUTABLE = config_obj.get('database_tables','treeotutable')
        setup_db.clear_single_table(connection,cursor,TREEOTUTABLE)
        print 'Preparing tree - otu association file'
        tree_otu_filename = prepare_otu_tree_file(connection,cursor,phy,taxonomy,args.nstudies)
        print 'Importing tree/otus'
        setup_db.import_csv_file(connection,cursor,TREEOTUTABLE,tree_otu_filename)
    except psy.Error as e:
        print e.pgerror
