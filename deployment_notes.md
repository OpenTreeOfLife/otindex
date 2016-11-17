Planning to test deployment using ansible playbooks rather than bash scripts.

Notes from reading ansible docs:

* While it may be common sense, it is worth sharing: Any management system benefits from being run near the machines being managed. If you are running Ansible in a cloud, consider running it from a machine inside that cloud. In most cases this will work better than on the open Internet.

## Notes from manual deployment

These instructions based on installing on a Duke research toolkits VM
(ubuntu 16.04.1 LTS)

Install and setup postgres; see [PostgreSQL installation instructions](https://help.ubuntu.com/community/PostgreSQL)

    $ sudo apt-get install postgresql postgresql-contrib
    $ sudo -u postgres psql postgres
    $ \password postgres  # then exit using \q
    $ sudo -u postgres createdb otindex  # create database

Install pip, virtualenv, apache, libpq-dev and create a virtual environment
    $ sudo apt-get install python-pip
    $ sudo apt-get install virtualenv
    $ sudo apt-get install libpq-dev
    $ sudo apt-get install apache2
    $ sudo apt-get install libapache2-mod-wsgi
    $ virtualenv opentree
    $ source opentree/bin/activate

Install git
    $ sudo apt-get install git-core

Install a local copy of the phylesystem
    $ mkdir phylesystem
    $ mkdir phylesystem/shards
    $ cd ~/phylesystem/shards
    $ git clone https://github.com/OpenTreeOfLife/phylesystem-1.git

Download a copy of OTT (substitute URL of current version):
    $ wget http://files.opentreeoflife.org/ott/ott2.10/ott2.10draft11.tgz
    $ tar xfvz ott2.10draft11.tgz

Set up peyotl, following the [installation and configuration instructions](http://opentreeoflife.github.io/peyotl/installation/). All operations run against local copies of phylesystem and OTT, do you do not need any of the API settings.

Run the peyotl tests:
    $ python setup.py test

Clone and setup the otindex repo
    $ git clone https://github.com/OpenTreeOfLife/otindex.git
    $ cd otindex
    $ pip install -r requirements.txt
    $ python setup.py install

Edit the otindex `config.yml` file for the local setup
    $ cd otindex/scripts
    $ cp config.yml.example config.yml
You will need to specify the postgres user (likely 'postgres'), DB password,
and ott location.

Set up and load the database
    $ bash run_setup_scripts.sh config.yml

Enable WSGI
  $ sudo a2enmod wsgi
  $ sudo /usr/sbin/apachectl restart

Set up the `production.ini` file:

Run the application

Run the tests
