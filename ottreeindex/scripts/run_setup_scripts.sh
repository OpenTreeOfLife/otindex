if ! [[ "$1" ]]; then
  echo "error: no config file provided"
  exit 1
fi

config=$1

# delete existing table, re-create
echo "python setup_db.py -d $config"
python setup_db.py -d $config

# load nexson files
echo "python load_nexsons.py $config"
python load_nexson.py $config

# load otu table
echo "python create_otu_table.py $config"
python create_otu_table.py $config

# run some simple tests
echo "python test_db_selects.py $config"
python test_db_selects.py $config
