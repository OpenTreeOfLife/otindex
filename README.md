# otindex

A pyramid + postgres implementation of a treestore index for Open Tree of Life.
Provides API access to the JSON files in the OpenTree 
[phylesystem](https://github.com/opentreeoflife/phylesystem) data store. 

These instructions assume you are doing development setup on your local
machine. For deploying otindex on a server, we have [ansible
playbook](https://github.com/OpenTreeOfLife/otindex_ansible).

## Tech used in development

* python 2.7.10
* [pyramid](http://www.pylonsproject.org/) v 1.5.7
* [postgres](http://www.postgresql.org/) v 9.5.2
* [peyotl](https://github.com/OpenTreeOfLife/peyotl): opentree python library for interacting with the opentree tree store

## Setup your postgres database
See the
[README](https://github.com/OpenTreeOfLife/otindex/blob/master/otindex/scripts/README.md)
file in that directory for more detailed setup information.
# Postgres setup ubuntu version (draft)
    sudo apt-get install postgresql  
    service postgresql start  
    sudo -u postgres createdb -O postgres -E utf8 otindex  
    sudo -u postgres createuser opentree -D -S -P  
    <create password>
    sudo su - postgres  
    psql otindex  
    otindex=> GRANT ALL ON DATABASE otindex TO opentree;

## Configuration

First copy the configuration template:

    `$ cp development-example.ini development.ini`

Then adjust the new file for your local settings:

* In the `connection_info` section, add the database username, database name  
  and password
* In the [app:main] section, edit `sqlalchemy.url` to match the settings in
  `connection_info`
* Optionally, change the logging level for various components

## Installation

**Install otindex and set up the database tables**

You probably want to be using a virtualenv.

```
$ pip install -r requirements.txt
$ python setup.py develop
$ initialize_otindex_db development.ini
```

where `initialize_otindex_db` is in the `bin` directory of your virtualenv.
This last step creates the database tables defined in `models.py`. It clears
any existing tables.

**Load data into the database**
The `otindex/scripts` directory contains scripts for loading data into the
database. See the
[README](https://github.com/OpenTreeOfLife/otindex/blob/master/otindex/scripts/README.md)
file in that directory for detailed setup information.

Note: if running locally, relies on "home/user/.peyotl/config" to find taxonomy and phylesystem
It will also write out logs to peyotl log file

cd otindex/scripts
bash run_setup_scripts.sh ../../development.ini 100



**Running the application**

In the top-level directory, run:

    $ pserve development.ini --reload

You should now be able to access the methods on `http://0.0.0.0:6543`.

**Running tests**

See TESTING.md in this repo.

## Development notes

The top-level `dev_scripts` directory contains scripts for testing out new
features. Some implement peyotl functions, while others allow database testing
from the CLI without deploying pyramid. No promises that anything in that
directory works property.
