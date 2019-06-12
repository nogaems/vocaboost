from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import auth

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(String)
    salt = Column(String)

    def __init__(self, username, password):
        self.username = username
        self.password, self.salt = auth.hashed_password(password)

    def __repr__(self):
        return 'User(username={})'.format(self.username)

    def to_dict(self):
        result = {}
        for column in self.__table__.columns:
            result[column.name] = str(getattr(self, column.name))
        return result
