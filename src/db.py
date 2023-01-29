import json

from sqlalchemy import create_engine, Column, String, DateTime, Integer, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlite3
from datetime import datetime
import json

DB_FILE = "db.sqlite3"

# Connect to the database
engine = create_engine(f'sqlite:///{DB_FILE}')
# engine = create_engine('postgresql://username:password@host:port/database')
Base = declarative_base()
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
db = SessionLocal()

class Namespace(Base):
    __tablename__ = "namespaces"

    id = Column(Integer, primary_key=True, index=True)
    chart_name = Column(String, index=True)
    chart_repo_url = Column(String, index=True)
    namespace = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __init__(self, namespace: str, chart_name: str, chart_repo_url: str):
        self.namespace = namespace
        self.chart_name = chart_name
        self.chart_repo_url = chart_repo_url
        self.created_at = datetime.now()




def get_connection():
    return sqlite3.connect(f'{DB_FILE}')


def create_namespace_record(chart_name, chart_repo_url, namespace):
    namespace = Namespace(chart_name=chart_name, chart_repo_url=chart_repo_url, namespace=namespace)
    db.add(namespace)
    db.commit()
    db.refresh(namespace)
    return namespace


def delete_namespace_record(namespace):
    db.query(Namespace).filter_by(namespace=namespace).delete()
    db.commit()


def get_all_namespaces():
    namespaces = []
    with sqlite3.connect(DB_FILE) as con:
        cur = con.cursor()
        cur.execute("SELECT namespace, chart_name, chart_repo_url, created_at FROM namespaces")
        rows = cur.fetchall()
        for row in rows:
            namespaces.append(
                {"namespace": row[0], "chart_name": row[1], "chart_repo_url": row[2], "created_at": row[3]})
    return namespaces


def delete_all_namespaces_from_db():
    c = conn.cursor()
    c.execute("DELETE from namespaces")
    conn.commit()
    conn.close()


def get_all_namespaces_from_db():
    c = conn.cursor()
    query = c.execute("SELECT namespace FROM namespaces")
    for ns in list(query):
        return ns

