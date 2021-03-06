import psycopg2 as psy
import sqlalchemy

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSON,JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import ProgrammingError

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    aliased,
    )

from otindex.models import (
    Study,
    Tree,
    Taxonomy,
    Curator,
    Property,
)

###### Queries ###############################

# recursive query; see
# http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.cte
def recursive_ott_query(ott_id,session):
    lineage = session.query(
        Taxonomy).filter(
            Taxonomy.id==ott_id
        ).cte(name="lineage",recursive=True)
    print "lineage1? ",type(lineage)

    ott_alias = aliased(Taxonomy,name='ott_alias')
    lineage_alias = aliased(lineage,name='lineage_alias')

    # lineage = lineage.union_all(
    #     session.query(
    #         ott_alias.id,
    #         ott_alias.name,
    #         ott_alias.parent
    #     ).filter(
    #         ott_alias.id==lineage_alias.c.parent
    #     )
    # )

    lineage = lineage.union_all(
        session.query(
            ott_alias
        ).filter(
            ott_alias.id==lineage_alias.c.parent
        )
    )
    print "lineage2? ",type(lineage)

    #q = session.query(lineage.c.parent,lineage.c.name).all()
    q = session.query(lineage).all()
    print "q? ",type(q)
    for row in q:
        print type(row),row

    taxon = session.query(Taxonomy).filter(
        Taxonomy.id==ott_id
        ).first()
    print "taxon? ",type(taxon)


def query_association_table(session):
    # property_value = 'Karen Cranston'
    # query_obj = session.query(
    #     Study.id
    # ).filter(
    #     Study.curators.any(name=property_value)
    #     ).all()
    # for row in query_obj:
    #     print row.id
    property_value = '81461'
    query_obj = session.query(
        Tree.study_id,
        Tree.tree_id
    ).filter(
        Tree.otus.any(id=property_value)
        ).all()
    for row in query_obj:
        print row.study_id,row.tree_id

def query_properties(session,type):
    properties = []
    query_obj = session.query(Property.property).filter(
        Property.type=='study'
    ).all()
    for row in query_obj:
        properties.append(row.property)
    # now add the non-JSON properties
    properties.append("ntrees")
    print "study properties: "
    for p in properties:
        print " ",p

    properties = []
    query_obj = session.query(Property.property).filter(
        Property.type=='tree'
    ).all()
    for row in query_obj:
        properties.append(row.property)
    # now add the non-JSON properties
    properties.append("ntips")
    properties.append("proposed")
    properties.append("treebase_id")
    print "tree properties: "
    for p in properties:
        print " ",p

def get_tree_query_object(session,verbose):
    query_obj = None
    if (verbose):
        # assigning labels like this makes it easy to build the response json
        # but can't directly access any particular item via the label,
        # i.e result.ot:studyId because of ':' in label
        query_obj = session.query(
            Tree.tree_id.label('ot:treeId'),
            Tree.study_id.label('ot:studyId'),
            Tree.proposed.label('ot:proposedForSynthesis'),
            Tree.data[('@label')].label('@label'),
            Tree.data[('^ot:branchLengthMode')].label('ot:branchLengthMode'),
            Tree.data[('^ot:branchLengthDescription')].label('ot:branchLengthDescription')
        )
    else:
        query_obj = session.query(
            Tree.study_id.label('ot:studyId'),
            Tree.tree_id.label('ot:treeId')
        )
    return query_obj

def get_study_return_props(session,studyid,studydict):
    slist =[
        "^ot:studyPublicationReference","^ot:curatorName",
        "^ot:studyYear","^ot:focalClade","^ot:focalCladeOTTTaxonName",
        "^ot:dataDeposit","^ot:studyPublication"
        ]
    # assigning labels like this makes it easy to build the response json
    # but can't directly access any particular item via the label,
    # i.e result.ot:studyId because of ':' in label
    query_obj = session.query(
        Study.id.label('ot:studyId'),
        Study.data[(slist[0])].label('ot:studyPublicationReference'),
        Study.data[(slist[1])].label('ot:curatorName'),
        Study.data[(slist[2])].label('ot:studyYear'),
        Study.data[(slist[3])].label('ot:focalClade'),
        Study.data[(slist[4])].label('ot:focalCladeOTTTaxonName'),
        Study.data[(slist[5])].label('ot:dataDeposit'),
        Study.data[(slist[6])].label('ot:studyPublication'),
    ).filter(
        Study.id == studyid
    )

    # should only be one row
    resultdict = {}
    for row in query_obj.all():
        for k,v in row._asdict().items():
            if v is not None:
                resultdict[k]=v
    studydict[studyid] = resultdict
    return studydict

def build_json_response(filtered,verbose=False):
    resultslist = []
    studydict = {}
    # run the query and build the response json
    for row in filtered.all():
        treedict = row._asdict()
        studyid = treedict['ot:studyId']
        if not studyid in studydict:
            # if this is the first time we have seen this study,
            # get either the studyid or the study properties and
            # add a blank list for the trees
            if (verbose):
                get_study_return_props(session,studyid,studydict)
            else:
                studydict[studyid] = {'ot:studyId':studyid}
            studydict[studyid]['matched_trees'] = []
        # add the tree properties to the list of matched trees
        studydict[studyid]['matched_trees'].append(treedict)
    for k,v in studydict.items():
        resultslist.append(v)
    return resultslist

def query_trees_by_study_id(session,study_id):
    #resultlist = []
    query_obj = get_tree_query_object(session,True)
    filtered = query_obj.filter(Tree.study_id == study_id)
    resp = build_json_response(filtered,True)
    print resp

# the tree queries involve joins on study table
def query_trees_by_json_field(session):
    property_type = '^ot:tag'
    property_value = 'ITS'

    trees = session.query(
        Tree.tree_id.label('ot:treeId'),
        Tree.study_id.label('ot:studyId'),
        Tree.data[('^ot:branchLengthMode')].label('ot:branchLengthMode'),
        Tree.data[('^ot:branchLengthDescription')].label('ot:branchLengthDescription')
    ).filter(
        Tree.data.contains({property_type:[property_value]})
    ).all()

    resultslist = []
    studydict = {}
    for row in trees:
        treedict = row._asdict()
        studyid = treedict['ot:studyId']
        if not studyid in studydict:
            # if this is the first time we have seen this study,
            # get the study properties and add a blank list for the trees
            get_study_properties(session,studyid,studydict)
            studydict[studyid]['matched_trees']=[]
        # add the tree properties to the list of matched trees
        studydict[studyid]['matched_trees'].append(treedict)
    for k,v in studydict.items():
        print "\nStudy",k
        print v
        resultslist.append(v)

def get_study_properties(session,studyid,studydict):
    slist =[
        "^ot:studyPublicationReference","^ot:curatorName",
        "^ot:studyYear","^ot:focalClade","^ot:focalCladeOTTTaxonName",
        "^ot:dataDeposit","^ot:studyPublication"
        ]
    # assigning labels like this makes it easy to build the response json
    # but can't directly access any particular item via the label,
    # i.e result.ot:studyId because of ':' in label
    query_obj = session.query(
        Study.id.label('ot:studyId'),
        Study.data[(slist[0])].label(slist[0]),
        Study.data[(slist[1])].label(slist[1]),
        Study.data[(slist[2])].label('ot:studyYear'),
        Study.data[(slist[3])].label('ot:focalClade'),
        Study.data[(slist[4])].label('ot:focalCladeOTTTaxonName'),
        Study.data[(slist[5])].label('ot:dataDeposit'),
        Study.data[(slist[6])].label('ot:studyPublication'),
    ).filter(
        Study.id == studyid
    )

    # should only be one row
    resultdict = {}
    for row in query_obj.all():
        for k,v in row._asdict().items():
            if v is not None:
                resultdict[k]=v
    studydict[studyid] = resultdict
    return studydict

def query_fulltext(session):
    property_type = '^ot:studyPublicationReference'
    # add wildcards to the property_value
    property_value = '%Smith%'
    study = session.query(Study).filter(
        Study.data[
            property_type
        ].astext.ilike(property_value)
    )
    print "studies with Smith in reference: ",study.count()

def query_int_or_string(session):
    # cases where the query might comes in as a string or integer
    # but needs to be a string

    # one with integer
    year = 2016
    study = session.query(Study).filter(
        Study.data[
            ('^ot:studyYear')
        ].astext.cast(sqlalchemy.Integer) == year
        )
    print "studies with int year = 2016: ",study.count()

    year = "2016"
    study = session.query(Study).filter(
        Study.data[
            ('^ot:studyYear')
        ].astext.cast(sqlalchemy.Integer) == year_str
        )
    print "studies with str year = 2016: ",study.count()

    focalClade = 765193
    clade_str = str(focalClade)
    study = session.query(Study).filter(
        Study.data[
            ('^ot:focalClade')
        ].cast(sqlalchemy.Integer) == focalClade
        )
    print "studies with focal clade = 765193: ",study.count()

def basic_jsonb_query(session):

    # one with string
    focalclade = 'Aves'
    study = session.query(Study).filter(
        Study.data[
            ('^ot:focalCladeOTTTaxonName')
        ].astext == focalclade
        )
    print "studies with focalclade=Aves: ",study.count()

    # doi, which is a path
    doi = 'http://dx.doi.org/10.1600/036364408785679851'
    study = session.query(Study).filter(
        Study.data[
            ('^ot:studyPublication','@href')
        ].astext == doi
        )
    print "studies with doi=http://dx.doi.org/10.1600/036364408785679851: ",study.count()

def test_filtering(session):
    list = ["^ot:studyYear","^ot:focalClade"]
    #for id,f,g in session.query(Study.id,Study.data[(list[0])],Study.data[(list[1])]):
    #    print id,f,g

    # test filtering
    starttime = dt.datetime.now()
    query_obj = session.query(
        Study.id.label('id'),
        Study.data[(list[0])].label('year'),
        Study.data[(list[1])].label('clade')
        )
    filtered = query_obj.filter(
        Study.data[
            ('^ot:studyYear')
            ].cast(sqlalchemy.Integer)==2016
        ).all()
    endtime = dt.datetime.now()
    #for row in filtered:
    #    for k,v in row._asdict().items():
    #        if v is not None:
    #            print '({label},{value})'.format(label=k,value=v)
    #print len(filtered)
    print "Query, then filter: ",endtime - starttime

    starttime = dt.datetime.now()
    query_obj = session.query(Study.id,Study.data[(list[0])],Study.data[(list[1])]).filter(
        Study.data[
            ('^ot:studyYear')
        ].cast(sqlalchemy.Integer)==2016
        ).all()
    endtime = dt.datetime.now()
    #print query_obj.count()
    print "Query and filter: ",endtime - starttime

def test_filter_strings(sesion):
    list = ["^ot:studyYear","^ot:focalClade"]
    # test filter strings
    query_obj = session.query(
        Study.id.label('id'),
        Study.data[(list[0])].label('year'),
        Study.data[(list[1])].label('clade')
        )
    #filter_string = "{type} = '{value}'".format(type='id',value='ot_159')
    filter_string = "Study.id = '{value}'".format(value='ot_159')
    filtered = query_obj.filter(text(filter_string))
    print filtered.count()

# def like_query(session):
#     # query.filter(User.name.like('%ed%'))
#     curatorName = "Cranston"

def query_trees_by_ott_id(session):
    #Aves
    ottid = 81461
    query_obj = session.query(
        Tree.study_id.label('ot:studyId'),
        Tree.tree_id.label('ot:treeId')
    )
    filtered = query_obj.filter(
        Tree.otus.any(id=ottid)
    )
    print "studies with id=81461",filtered.count()


def value_in_array(session):
    print "testing tag query; looking for value in list"
    #tag = 'cpDNA'
    tag = 500
    property_value = [tag]
    property_type = "^ot:tag"
    searchdict = {property_type:property_value}
    studies = session.query(Study).filter(
        #Study.data.contains('{"^ot:tag":["cpDNA"]}')
        #Study.data.contains(searchdict)
        Study.data.contains({property_type:[tag]})
        )
    print "studies with tag=cpDNA",studies.count()

def test_joins(session):
    print "test_joins"
    # sqlstring: select curator_study_map.study_id
    #   from curator_study_map
    #   join curator on curator.id=curator_study_map.curator_id
    #   where curator.name='Karen Cranston';
    curatorName = 100
    query_obj = session.query(
            Study.id
        ).filter(Study.curators.any(name=curatorName))
    print "studies for {c}".format(c=curatorName)
    for row in query_obj.all():
        print row.id

    studyid = "ot_159"
    query_obj = session.query(
            Curator.name
        ).filter(Curator.studies.any(id=studyid))
    print "curators for {s}".format(s=studyid)
    for row in query_obj.all():
        print row.name

def all_tags(session):
    # the jsonb query is select distinct jsonb_extract_path(data,'^ot:tag') from {table};
    # where table = tree or study
    # note that ot:tag is a list, so the return from the query is the distinct
    # tag lists, not the distinct individual tags, so must process
    tree_tags = set()
    study_tags = set()
    query_obj1 = session.query(Study.data['^ot:tag'].label('tag')).distinct()
    for row in query_obj1.all():
        if row.tag is None:
            continue
        study_tags.update(row.tag)
        # if (isinstance(row.tag,basestring)):
        #      print row.tag
        # else:
    print "{n} unique study tags".format(n=len(study_tags))
    query_obj2 = session.query(Tree.data['^ot:tag'].label('tag')).distinct()
    for row in query_obj2.all():
        if row.tag is None:
            continue
        tree_tags.update(row.tag)
        # if (isinstance(row.tag,basestring)):
        #      print row.tag
        # else:
    print "{n} unique tree tags".format(n=len(tree_tags))

    #return {'tree_tags':tree_tags,'study_tags':study_tags}

if __name__ == "__main__":
    connection_string = 'postgresql://postgres@localhost/otindex'
    db = sqlalchemy.create_engine(connection_string)
    engine = db.connect()
    meta = sqlalchemy.MetaData(engine)
    SessionFactory = sessionmaker(engine)
    session = SessionFactory()

    try:
        # test_joins(session)
        # value_in_array(session)
        # query_int_or_string(session)
        # basic_jsonb_query(session)
        # query_fulltext(session)
        # query_trees_by_study_id(session,'ot_55')
        # all_tags(session)
        #recursive_ott_query(691846,session)
        query_association_table(session)
        # print "study props:"
        # query_properties(session,'study')
        # print "tree props:"
        # query_properties(session,'tree')
    except ProgrammingError as e:
        print e.message
