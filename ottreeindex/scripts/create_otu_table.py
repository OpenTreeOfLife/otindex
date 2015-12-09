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

def create_phylesystem_obj():
    # create connection to local phylesystem
    phylesystem_api_wrapper = PhylesystemAPI(get_from='local')
    phylesystem = phylesystem_api_wrapper.phylesystem_obj
    return phylesystem

def getTreeID(cursor,study_id,tree_label):
    sqlstring = ('SELECT id FROM {tablename} '
        'WHERE study_id=%s and tree_label=%s;'
        .format(tablename='tree')
        )
    data = (study_id,tree_label)
    print '  SQL: ',cursor.mogrify(sqlstring,data)
    cursor.execute(sqlstring,data)
    return cursor.fetchone()[0]

def print_otu_file(connection,cursor,phy,nstudies=None):
    filename = "tree_otu_mapping.csv"
    with open (filename,'w') as f:
        # datafile format is 'ottid'\t'treeid' where treeid is not
        # the treeid (string) in the nexson, but the treeid (int) from
        # the database for faster indexing
        counter = 0
        for study_id, n in phy.iter_study_objs():
            print study_id
            otu_dict = gen_otu_dict(n)
            mapped_otus = {}
            # iterate over the OTUs in the study, collecting
            # the mapped ones
            for oid, o in otu_dict.items():
                label = o['^ot:originalLabel']
                ottname = o.get('^ot:ottTaxonName')
                if ottname is not None:
                    ottID = o.get('^ot:ottId')
                    otu_props = [ottname,ottID]
                    mapped_otus[oid]=otu_props
                    print oid,ottID,label,ottname

            # now iterate over trees and collect OTUs used in
            # each tree
            for trees_group_id, tree_label, tree in iter_trees(n):
                tree_id = getTreeID(cursor,study_id,tree_label)
                if (tree_id is None):
                    raise LookupError('tree_id for study {s}, tree {t}'
                        ' not found'.format(s=study_id,t=tree_label))
                for node_id, node in iter_node(tree):
                    oid = node.get('@otu')
                    # no @otu property on internal nodes
                    if oid is not None:
                        otu_props = mapped_otus.get(oid)
                        if otu_props is not None:
                            ottname = otu_props[0]
                            ottID = otu_props[1]
                            print tree_label,oid,ottID,ottname
                            f.write('{t},{o}\n'.format(t=tree_id,o=ottID))

            counter+=1
            if (nstudies and counter>=nstudies):
                f.close()
                break
    return filename

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
    config_dict={}
    with open(args.configfile,'r') as f:
        config_dict = yaml.safe_load(f)

    connection, cursor = setup_db.connect(config_dict)
    phy = create_phylesystem_obj()
    print_otu_file(connection,cursor,phy,args.nstudies)
