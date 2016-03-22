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
    config.add_route('home', '/')

    # v2 methods (oti behaviour)
    config.add_route('find_studies_v2','/v2/find_studies')
    config.add_route('find_trees_v2','/v2/find_trees')
    config.add_route('properties_v2','/v2/properties')
    config.add_route('add_update_studies_v2','/v2/add_update_studies')
    config.add_route('remove_studies_v2','/v2/remove_studies')

    # v3 methods
    config.add_route('find_studies','/v3/find_studies')
    config.add_route('find_trees','/v3/find_trees')
    config.add_route('properties','/v3/properties')
    config.scan()
    return config.make_wsgi_app()
