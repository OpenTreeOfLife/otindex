**NOTE**: These are notes only, not instructions. See the READMEs in this repo
for documentation.

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

Edit the otindex `development.yml` file for the local setup
    $ cp development-example.ini development.ini
You will need to specify the postgres user (likely 'postgres'), DB name, and DB
password.

Set up and load the database
    $ bash run_setup_scripts.sh config.yml

Apache configuration based on:
http://docs.pylonsproject.org/projects/pyramid/en/latest/tutorials/modwsgi/

Enable WSGI
  $ sudo a2enmod wsgi
  $ sudo /usr/sbin/apachectl restart

Set up the `production.ini` file:

Run the application

Run the tests

# Deploying on AWS

* Select Debian from Community AMIs: `debian-jessie-amd64-hvm-2016-09-19-ebs - ami-2a34e94a`
* Select instance: m3.medium
* Select the security group: 'OpenTree... with ping' for development and 'OpenTree production' for production. Note that you can't change the security group after launch!
* Choose key pair: 'opentree' for dev, 'opentree production' for production
* log in and accept the fingerprint prompt:

      ssh -i <pem file> admin@<hostname>
* edit the ansible playbook with the IP address of the EC2 host
* run ansible, where server is either `production` or `development`:

      ansible-playbook otindex.yml -i hosts --limit <server>
* run the tests (see TESTING.md)
