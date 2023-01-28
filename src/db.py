from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlite3
from datetime import datetime

DB_FILE = "db.sqlite3"

# Connect to the database
engine = create_engine(f'sqlite:///{DB_FILE}')
# engine = create_engine('postgresql://username:password@host:port/database')
Base = declarative_base()
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()


class Namespace(Base):
    __tablename__ = 'namespaces'
    id = Column(Integer, primary_key=True, index=True)
    namespace = Column(String, index=True)
    chart_name = Column(String)
    chart_repo_url = Column(String)
    created_at = Column(String, default=datetime.utcnow)

    def __init__(self, namespace: str, chart_name: str, chart_repo_url: str):
        self.namespace = namespace
        self.chart_name = chart_name
        self.chart_repo_url = chart_repo_url
        self.created_at = datetime.now()


Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
db = Session()


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
