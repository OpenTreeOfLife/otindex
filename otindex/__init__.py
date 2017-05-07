from pyramid.config import Configurator
from sqlalchemy import engine_from_config
# from paste.translogger import TransLogger

import yaml

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
    v = '{api_version:v1|v2|v3|v4}'
    config.add_route('find_studies','/{v}/studies/find_studies'.format(v=v),request_method="POST")
    config.add_route('find_trees','/{v}/studies/find_trees'.format(v=v),request_method="POST")
    config.add_route('properties','/{v}/studies/properties'.format(v=v),request_method="POST")
    config.add_route('add_update','{v}/studies/add_update'.format(v=v))
    config.add_route('remove','{v}/studies/remove'.format(v=v))
    config.add_route('about','{v}/studies/about'.format(v=v))

    config.scan()
    return config.make_wsgi_app()
    # app = config.make_wsgi_app()
    # app = TransLogger(app, setup_console_handler=False)
    # return app
