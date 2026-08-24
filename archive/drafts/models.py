from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Track(Base):
    __tablename__ = 'tracks'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    artist = Column(String)
    album = Column(String)
    duration = Column(Float)

    def __init__(self, title, artist, album, duration):
        self.title = title
        self.artist = artist
        self.album = album
        self.duration = duration

class Album(Base):
    __tablename__ = 'albums'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    artist = Column(String)

    tracks = relationship('Track', back_populates='album')

    def __init__(self, name, artist):
        self.name = name
        self.artist = artist
