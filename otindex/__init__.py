from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.request import Response
from sqlalchemy import engine_from_config
# from paste.translogger import TransLogger
import logging
import yaml

from .models import (
    DBSession,
    Base,
    )


_LOG = logging.getLogger(__name__)

def request_factory(environ):
    """Factory function that adds the headers necessary for Cross-domain calls.

    Adapted from:
       http://stackoverflow.com/questions/21107057/pyramid-cors-for-ajax-requests
    Copied from mtholder/pyraphyletic
    """
    request = Request(environ)
    _LOG.debug('trunctated request body: {b}'.format(b=request.body[:1000]))
    return request

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.include('.cors')
    config.add_cors_preflight_handler()
    config.include('pyramid_chameleon')
    config.set_request_factory(request_factory)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    v = '{api_version:v1|v2|v3|v4}'
    config.add_route('find_studies','{v}/studies/find_studies'.format(v=v),request_method="POST")
    config.add_route('find_trees','{v}/studies/find_trees'.format(v=v),request_method="POST")
    config.add_route('properties','{v}/studies/properties'.format(v=v),request_method="POST")
    config.add_route('add_update','{v}/studies/add_update'.format(v=v),request_method="POST")
    config.add_route('remove','{v}/studies/remove'.format(v=v))
    config.add_route('about','{v}/studies/about'.format(v=v))
    config.add_route('parse_phylesystem_webhook','{v}/studies/phylesystem_webhook'.format(v=v), request_method="POST")
 #   config.add_route('parse_amendment_webhook','{v}/studies/amendment_webhook'.format(v=v), request_method="POST")

    config.scan()
    return config.make_wsgi_app()
    # app = config.make_wsgi_app()
    # app = TransLogger(app, setup_console_handler=False)
    # return app
