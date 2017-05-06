from pyramid.config import Configurator
from sqlalchemy import engine_from_config
# from paste.translogger import TransLogger

import yaml

from .models import (
    DBSession,
    Base,
    )

def request_factory(environ):
    """Factory function that adds the headers necessary for Cross-domain calls.

    Adapted from:
       http://stackoverflow.com/questions/21107057/pyramid-cors-for-ajax-requests
    """
    request = Request(environ)
    if request.is_xhr:
        request.response = Response()
        request.response.headerlist = []
        request.response.headerlist.extend(
            (
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Credentials', 'true'),
                ('Access-Control-Max-Age', 86400),
                ('Content-Type', 'application/json')
            )
        )
    return request

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.include('pyramid_chameleon')
    config.set_request_factory(request_factory)

    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')

    # OPTIONS
    config.add_route('options', '/', request_method='OPTIONS')

    config.add_route('find_studies','/v3/studies/find_studies',request_method="POST")
    config.add_route('find_trees','/v3/studies/find_trees',request_method="POST")
    config.add_route('properties','/v3/studies/properties',request_method="POST")
    config.add_route('add_update','v3/studies/add_update')
    config.add_route('remove','v3/studies/remove')
    config.add_route('about','v3/studies/about')

    config.scan()
    return config.make_wsgi_app()
    # app = config.make_wsgi_app()
    # app = TransLogger(app, setup_console_handler=False)
    # return app
