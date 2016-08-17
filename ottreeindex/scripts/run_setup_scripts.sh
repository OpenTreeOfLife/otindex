# first arg is config file
if ! [[ "$1" ]]; then
  echo "error: no config file provided"
  exit 1
fi

# second (optional) arg is nstudies limit
if [ "$2" ]; then
    nstudies=$2
    echo $nstudies
fi

config=$1

if [ $nstudies ]; then
    # delete existing tables, re-create
    python setup_db.py -d $config

    # load nexson files
    python load_nexson.py $config -n $nstudies

    # load taxonomy
    python load_taxonomy.py $config

    # load otu table
    python create_otu_table.py $config -n $nstudies

    # run some simple tests
    python test_db_selects.py $config

    exit 0
fi

# delete existing table, re-create
python setup_db.py -d $config

# load nexson files
python load_nexson.py $config

# load taxonomy
python load_taxonomy.py $config

# load otu table
python create_otu_table.py $config

# run some simple tests
python test_db_selects.py $config
