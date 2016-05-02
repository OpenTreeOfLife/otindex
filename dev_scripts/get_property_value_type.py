# verifies which study-level and tree-level properties
# can be lists

# peyotl setup
from peyotl.phylesystem.phylesystem_umbrella import Phylesystem
from peyotl.api.phylesystem_api import PhylesystemAPI
from peyotl.manip import iter_trees
from peyotl.nexson_syntax import get_nexml_el

def create_phylesystem_obj():
    # create connection to local phylesystem
    phylesystem_api_wrapper = PhylesystemAPI(get_from='local')
    phylesystem = phylesystem_api_wrapper.phylesystem_obj
    return phylesystem

if __name__ == "__main__":
    counter = 0
    limit = None
    studyprops = [line.rstrip('\n') for line in open('study_properties.txt')]
    studyPropsCanBeLists = set()
    treeprops = [line.rstrip('\n') for line in open('tree_properties.txt')]
    treePropsCanBeLists = set()
    phy = create_phylesystem_obj()
    for study_id, studyobj in phy.iter_study_objs():
        for prop in studyprops:
            if prop in studyobj['nexml']:
                value = studyobj['nexml'][prop]
                if isinstance(value,list):
                    studyPropsCanBeLists.add(prop)
        for trees_group_id, tree_id, tree in iter_trees(studyobj):
            for prop in treeprops:
                if prop in tree:
                    value = tree[prop]
                    if isinstance(value,list):
                        treePropsCanBeLists.add(prop)
        counter+=1
        if (counter%100 == 0):
            print "Read {n} studies".format(n=counter)
        if (limit and counter>limit):
            break
    # print properites that can be lists
    print "found {n} study properties that are sometimes lists".format(n=len(studyPropsCanBeLists))
    for k in studyPropsCanBeLists:
        print k
    # print tree properites
    print "found {n} tree properties that are sometimes lists".format(n=len(treePropsCanBeLists))
    for k in treePropsCanBeLists:
        print k
