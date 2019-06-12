from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from sanic import Sanic
from api import api

from secrets import token_hex

import config
import model
import auth

if __name__ == '__main__':
    engine = create_engine(config.db_uri, echo=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    model.Base.metadata.create_all(engine)

    app = Sanic(__name__)
    app.blueprint(api, version=1)
    app.jwt_secret = token_hex(auth.jwt_secret_length)

    app.session = session
    app.run(host=config.host, port=config.port, debug=config.debug)

    session.close_all()
