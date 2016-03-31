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

    # v2/v3 methods (oti behaviour)
    config.add_route('find_studies_v3','/v3/studies/find_studies',request_method="POST")
    config.add_route('find_trees_v3','/v3/studies/find_trees',request_method="POST")
    config.add_route('properties_v3','/v3/studies/properties',request_method="POST")
    config.add_route('add_update_studies_v3','v3/add_update_studies')
    config.add_route('remove_studies_v3','v3/remove_studies')

    # v4 methods (new! improved!)
    config.add_route('about','/v4/studies/about')
    config.add_route('find_studies','/v4/find_studies')
    config.add_route('find_trees','/v4/find_trees')
    config.add_route('properties','/v4/properties')
    config.scan()
    return config.make_wsgi_app()
