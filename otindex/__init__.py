from pyramid.config import Configurator
from sqlalchemy import engine_from_config

import yaml
import pprint

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

    config.add_route('find_studies','/v3/studies/find_studies',request_method="POST")
    config.add_route('find_trees','/v3/studies/find_trees',request_method="POST")
    config.add_route('properties','/v3/studies/properties',request_method="POST")
    config.add_route('add_update','v3/studies/add_update')
    config.add_route('remove','v3/studies/remove')
    config.add_route('about','v3/studies/about')

    config.scan()
    return config.make_wsgi_app()

# see http://modwsgi.readthedocs.io/en/develop/user-guides/debugging-techniques.html
class LoggingMiddleware:

    def __init__(self, main):
        self.__main = main

    def __call__(self, environ, start_response):
        errors = environ['wsgi.errors']
        pprint.pprint(('REQUEST', environ), stream=errors)

        def _start_response(status, headers, *args):
            pprint.pprint(('RESPONSE', status, headers), stream=errors)
            return start_response(status, headers, *args)

        return self.__main(environ, _start_response)

main = LoggingMiddleware(main)
