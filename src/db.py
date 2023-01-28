from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlite3
# Connect to the database
engine = create_engine('sqlite:///test.db')
# engine = create_engine('postgresql://username:password@host:port/database')
Base = declarative_base()


class Namespace(Base):
    __tablename__ = 'namespaces'
    id = Column(Integer, primary_key=True)
    chart_name = Column(String)
    chart_repo = Column(String)
    name = Column(String)


Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
session = Session()


def create_namespace_record(chart_name: str, chart_repo: str, namespace: str):
    ns_record = Namespace(chart_name=chart_name, chart_repo=chart_repo, name=namespace)
    session.add(ns_record)
    session.commit()
