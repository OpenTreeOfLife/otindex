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

# use the bulk copy method to upload from the file into the table
def import_csv_file(connection,cursor,table,filename):
    print "copying {f} into {t} table".format(f=filename,t=table)
    with open (filename,'r') as f:
        copystring="COPY {t} FROM STDIN WITH CSV HEADER".format(t=table)
        cursor.copy_expert(copystring,f)
        connection.commit()

# All mapped OTUs in all studies
def prepare_csv_files(connection,cursor,phy,taxonomy,nstudies=None):
    otu_filename = "otu_mapping.csv"
    tree_otu_filename = "tree_otu_assoc.csv"
    seen_otus = {}
    with open(otu_filename, 'w') as f, open(tree_otu_filename, 'w') as g:
        fwriter = csv.writer(f)
        gwriter = csv.writer(g)
        # datafile format is 'ottid'\t'treeid' where treeid is not
        # the treeid (string) in the nexson, but the treeid (int) from
        # the database for faster indexing
        counter = 0
        fwriter.writerow(('id','name'))
        for study_id, n in phy.iter_study_objs():
            otu_dict = gen_otu_dict(n)
            # iterate over the OTUs in the study, collecting
            # the mapped ones
            mapped_otus = {}
            for oid, o in otu_dict.items():
                ottID = o.get('^ot:ottId')
                if ottID is not None:
                    label = o['^ot:originalLabel']
                    ottname = o.get('^ot:ottTaxonName')
                    if ottname is None:
                        ottname = 'unnamed'
                    if ottID not in seen_otus:
                        fwriter.writerow((ottID,ottname))
                        seen_otus[ottID] = ottname
                    otu_props = (ottname,ottID)
                    mapped_otus[oid] = otu_props

            # iterate over the trees in the study, collecting
            # tree/otu associations (including lineage)
            for trees_group_id, tree_id, tree in iter_trees(n):
                # the unique identifier in the tree table is an auto-incrementing
                # int, not the tree_id in the nexson, which is not unique
                tree_int_id = getTreeID(cursor,study_id,tree_id)
                ottIDs = {}     # all ids for this tree
                for node_id, node in iter_node(tree):
                    oid = node.get('@otu')
                    # no @otu property on internal nodes
                    if oid is not None:
                        otu_props = mapped_otus.get(oid)
                        if otu_props is not None:
                            ottID = otu_props[1]
                            ottIDs[ottID] = True
                            #print tree_id,oid,ottID
                ottIDs = parent_closure(ottIDs,taxonomy)
                for ottID in ottIDs:
                    if ottID not in seen_otus:
                        ottname = 'tbd'    # fix later, see peyotl issue
                        fwriter.writerow((ottID,ottname))
                        seen_otus[ottID] = ottname
                    gwriter.writerow((tree_int_id,ottID))

            counter+=1
            if (counter%500 == 0):
                print " prepared",counter,"studies"
            if (nstudies and counter>=nstudies):
                f.close()
                g.close()
                break
    return (otu_filename, tree_otu_filename)

def parent_closure(ottIDs,taxonomy):
    newids = {}
    for ottID in ottIDs:
        nextid = ottID
        while True:
            newids[nextid] = True
            if taxonomy == None: break
            nextid = taxonomy.ott_id2par_ott_id.get(nextid)
            if nextid == None:
                break
    return newids


def print_tree_otu_file(connection,cursor,phy,taxonomy,nstudies=None):
    filename = "tree_otu_mapping.csv"
    with open (filename,'w') as f:
        # datafile format is 'ottid'\t'treeid' where treeid is not
        # the treeid (string) in the nexson, but the treeid (int) from
        # the database for faster indexing
        counter = 0
        f.write('{t},{o}\n'.format(t='tree_int_id',o='ottID'))
        for study_id, n in phy.iter_study_objs():
            otu_dict = gen_otu_dict(n)
            mapped_otus = {}
            # iterate over the OTUs in the study, collecting
            # the mapped ones
            for oid, o in otu_dict.items():
                ottID = o.get('^ot:ottId')
                if ottID is not None:
                    label = o['^ot:originalLabel']
                    ottname = o.get('^ot:ottTaxonName')
                    if ottname is not None:
                        ottname = 'unnamed'
                    otu_props = [ottname,ottID]
                    mapped_otus[oid]=otu_props
                    #print oid,ottID,label,ottname
            # now iterate over trees and collect OTUs used in
            # each tree
            for trees_group_id, tree_id, tree in iter_trees(n):
                tree_int_id = getTreeID(cursor,study_id,tree_id)
                ottIDs = {}
                for node_id, node in iter_node(tree):
                    oid = node.get('@otu')
                    # no @otu property on internal nodes
                    if oid is not None:
                        otu_props = mapped_otus.get(oid)
                        if otu_props is not None:
                            ottID = otu_props[1]
                            ottIDs[ottID] = True
                            #print tree_id,oid,ottID
                            f.write('{t},{o}\n'.format(t=tree_int_id,o=ottID))
                ottIDs = parent_closure(ottIDs,taxonomy)
                for ottID in ottIDs:
                    f.write('{t},{o}\n'.format(t=tree_int_id,o=ottID))
            counter+=1
            if (counter%500 == 0):
                print " printed",counter,"studies"
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

    ott_loc = config_dict['taxonomy']
    if ott_loc == 'None':
        print 'No taxonomy'
        taxonomy = None
    else:
        taxonomy = ott.OTT(ott_loc)

    connection, cursor = setup_db.connect(config_dict)
    phy = create_phylesystem_obj()
    try:
        OTUTABLE = config_dict['tables']['otutable']
        TREEOTUTABLE = config_dict['tables']['treeotutable']
        print 'Preparing CSV files'
        (otu_filename, tree_otu_filename) = prepare_csv_files(connection,cursor,phy,taxonomy,args.nstudies)
        print 'Importing otus'
        import_csv_file(connection,cursor,OTUTABLE,otu_filename)
        print 'Importing tree/otus'
        import_csv_file(connection,cursor,TREEOTUTABLE,tree_otu_filename)
    except psy.Error as e:
        print e.pgerror
