#!/usr/bin/env python3

# a quite bit of pure suffering here
import os
import sys

src = 'src'
path = os.path.dirname(os.path.realpath(
    os.path.join(os.getcwd(), os.path.expanduser(__file__))))
parent = os.path.normpath(os.path.join(path, '..'))
src = os.path.join(parent, src)

os.chdir(src)
sys.path.append(src)

# now we're able to use our modules normally
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


import model
import config_test as config

engine = create_engine(config.db_uri, echo=config.sql_debug)
Session = sessionmaker(bind=engine)
session = Session()
model.Base.metadata.create_all(engine)
user = session.query(model.User).filter_by(username='test').first()
if not user:
    session.add(model.User('test', 'test'))
    session.commit()
