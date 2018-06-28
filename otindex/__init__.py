from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.request import Response
from sqlalchemy import engine_from_config
from pyramid.security import NO_PERMISSION_REQUIRED
# from paste.translogger import TransLogger
import logging
import yaml


from .models import (
    DBSession,
    Base,
    )


_LOG = logging.getLogger(__name__)



#from https://gist.github.com/kamalgill/b1f682dbdc6d6df4d052#file-cors-py

def includeme(config):
    config.add_directive(
        'add_cors_preflight_handler', add_cors_preflight_handler)
    config.add_route_predicate('cors_preflight', CorsPreflightPredicate)

    config.add_subscriber(add_cors_to_response, 'pyramid.events.NewResponse')

class CorsPreflightPredicate(object):
    def __init__(self, val, config):
        self.val = val

    def text(self):
        return 'cors_preflight = %s' % bool(self.val)

    phash = text

    def __call__(self, context, request):
        if not self.val:
            return False
        return (
            request.method == 'OPTIONS' and
            'Origin' in request.headers and
            'Access-Control-Request-Method' in request.headers
        )

def add_cors_preflight_handler(config):
    config.add_route(
        'cors-options-preflight', '/{catch_all:.*}',
        cors_preflight=True,
    )
    config.add_view(
        cors_options_view,
        route_name='cors-options-preflight',
        permission=NO_PERMISSION_REQUIRED,
    )

def add_cors_to_response(event):
    request = event.request
    response = event.response
    if 'Origin' in request.headers:
        response.headers['Access-Control-Expose-Headers'] = (
            'Content-Type,Date,Content-Length,Authorization,X-Request-ID')
        response.headers['Access-Control-Allow-Origin'] = (
            request.headers['Origin'])
        response.headers['Access-Control-Allow-Credentials'] = 'true'

def cors_options_view(context, request):
    response = request.response
    if 'Access-Control-Request-Headers' in request.headers:
        response.headers['Access-Control-Allow-Methods'] = (
            'OPTIONS,HEAD,GET,POST,PUT,DELETE')
    response.headers['Access-Control-Allow-Headers'] = (
        'Content-Type,Accept,Accept-Language,Authorization,X-Request-ID')
    return response


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.include('.cors')
    
     # make sure to add this before other routes to intercept OPTIONS
    config.add_cors_preflight_handler()

    config.include('pyramid_chameleon')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    v = '{api_version:v1|v2|v3|v4}'
    config.add_route('find_studies','{v}/studies/find_studies'.format(v=v),request_method="POST")
    config.add_route('find_trees','{v}/studies/find_trees'.format(v=v),request_method="POST")
    config.add_route('properties','{v}/studies/properties'.format(v=v),request_method="POST")
    config.add_route('add_update','{v}/studies/add_update'.format(v=v))
    config.add_route('remove','{v}/studies/remove'.format(v=v))
    config.add_route('about','{v}/studies/about'.format(v=v))

    config.scan()
    return config.make_wsgi_app()
    # app = config.make_wsgi_app()
    # app = TransLogger(app, setup_console_handler=False)
    # return app
