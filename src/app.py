#!/usr/bin/env python3
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from sanic import Sanic
from api import api

from faptcha import captcha

from secrets import token_hex
import argparse
import os
import imp

import model
import auth

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Main entry point')
    parser.add_argument('--config', '-c', dest='config',
                        action='store', default='config_test.py')
    args = parser.parse_args()
    config_file = os.path.expanduser(args.config)
    if not os.path.isfile(config_file):
        raise FileNotFoundError(
            'Configuration file \'{}\' doesn\'t exist'.format(config_file))
    try:
        config = imp.load_source('config', config_file)
    except Exception as e:
        raise ImportError(
            'Specified configuration file doesn\'t seem to be a correct python file')
    engine = create_engine(config.db_uri, echo=config.sql_debug)
    Session = sessionmaker(bind=engine)
    session = Session()
    model.Base.metadata.create_all(engine)

    app = Sanic(__name__)
    app.blueprint(api, version=1)
    app.jwt_secret = token_hex(auth.jwt_secret_length)

    app.session = session
    app.captcha = captcha.Captcha()
    app.cfg = config
    app.run(host=config.host, port=config.port, debug=config.sanic_debug)

    session.close_all()
