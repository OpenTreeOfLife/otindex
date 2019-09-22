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
    python setup_db.py $config

    # load nexson files
    python load_nexson.py $config -n $nstudies

    # prepare taxonomy files
    python generate_taxonomy_files.py $config -n $nstudies

    # load taxonomy files
    python load_taxonomy_files.py $config .

    # run some simple tests
    python test_db_selects.py $config

    exit 0
fi

# clear existing tables
python setup_db.py $config

# load nexson files
python load_nexson.py $config

# load taxonomy
python generate_taxonomy_files.py $config

# load otu table
python load_taxonomy_files.py $config .

# run some simple tests
python test_db_selects.py $config
