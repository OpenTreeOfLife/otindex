from pyramid.config import Configurator
from sqlalchemy import engine_from_config

import yaml

from .models import (
    DBSession,
    Base,
    )

def read_config(configfile):
    with open(configfile,'r') as f:
        config_dict = yaml.safe_load(f)
        return config_dict

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    db_secrets = read_config(settings['dbconfig.file'])
    if 'password' in db_secrets:
        settings['sqlalchemy.url'] = settings['sqlalchemy.url'] % (dbpass,)
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.include('pyramid_chameleon')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')

    config.add_route('find_studies','/v3/studies/find_studies',request_method="POST")
    config.add_route('find_trees','/v3/studies/find_trees',request_method="POST")
    config.add_route('properties','/v3/studies/properties',request_method="POST")
    config.add_route('add_update','v3/studies/add_update')
    config.add_route('remove','v3/studies/remove')
    config.add_route('about','v3/studies/about')

    config.scan()
    return config.make_wsgi_app()
