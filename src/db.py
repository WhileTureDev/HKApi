import click
from sqlalchemy import create_engine, Column, String, DateTime, Integer, inspect
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
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
db = SessionLocal()


class Namespace(Base):
    __tablename__ = "namespaces"

    id = Column(Integer, primary_key=True, index=True)
    chart_name = Column(String, index=True)
    chart_repo_url = Column(String, index=True)
    namespace = Column(String, index=True)
    install_type = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __init__(self, chart_name: str, chart_repo_url: str, namespace: str, install_type: str):
        self.chart_name = chart_name
        self.chart_repo_url = chart_repo_url
        self.namespace = namespace
        self.install_type = install_type
        self.created_at = datetime.now()


def get_connection():
    return sqlite3.connect(f'{DB_FILE}')


# def create_namespace_record_new(chart_name, chart_repo_url, namespace, install_type="new"):
#     namespace = Namespace(chart_name=chart_name, chart_repo_url=chart_repo_url, namespace=namespace,
#                           install_type=install_type)
#     db.add(namespace)
#     db.commit()
#     db.refresh(namespace)
#     return namespace

def create_namespace_record(chart_name, chart_repo_url, namespace):
    if not inspect(engine).has_table("namespaces"):
        Base.metadata.create_all(engine)
    existing_namespace = db.query(Namespace).filter_by(namespace=namespace).filter_by(install_type="new").first()
    ns = []
    if existing_namespace:
        exist_namespace = Namespace(chart_name=chart_name,
                                    chart_repo_url=chart_repo_url,
                                    namespace=namespace,
                                    install_type="upgrade")
        ns.append(exist_namespace)
        db.add(exist_namespace)
        db.commit()
        db.refresh(exist_namespace)
    else:
        new_namespace = Namespace(chart_name=chart_name,
                                  chart_repo_url=chart_repo_url,
                                  namespace=namespace,
                                  install_type="new")
        ns.append(new_namespace)
        db.add(new_namespace)
        db.commit()
        db.refresh(new_namespace)
    return ns


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
    # conn.close()


def get_all_namespaces_from_db():
    c = conn.cursor()
    query = c.execute("SELECT namespace FROM namespaces")
    namespaces = []
    for ns in list(query):
        for s in ns:
            s.replace("()'", '')
            namespaces.append(s)
    namespaces = list(dict.fromkeys(namespaces))
    return namespaces
