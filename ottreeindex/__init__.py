from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from .models import (
    DBSession,
    Base,
    )


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.include('pyramid_chameleon')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/v1')
    config.add_route('find_studies','/v1/find_studies')
    config.add_route('find_trees','/v1/find_trees')
    config.add_route('properties','/v1/properties')
    config.add_route('update_studies','v1/update_studies')
    config.scan()
    return config.make_wsgi_app()
