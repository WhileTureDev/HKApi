from datetime import datetime
import os

from sqlalchemy import create_engine, Column, String, DateTime, Integer, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

psq_pass = os.getenv("POSTGRES_PASSWORD")
Base = declarative_base()


class Deployment(Base):
    __tablename__ = 'deployments'

    id = Column(Integer, primary_key=True, index=True)
    chart_name = Column(String, index=True)
    chart_repo_url = Column(String, index=True)
    namespace = Column(String, index=True)
    install_type = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Connect to the database
engine = create_engine(f'postgresql://postgres:{psq_pass}@postgress-postgresql:5432/deployments')
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = sessionmaker(bind=engine)
session = Session()
db = SessionLocal()


# def __init__(self, chart_name: str, chart_repo_url: str, namespace: str, install_type: str):
#     self.chart_name = chart_name
#     self.chart_repo_url = chart_repo_url
#     self.namespace = namespace
#     self.install_type = install_type
#     self.created_at = datetime.now()


# def create_namespace_record_new(chart_name, chart_repo_url, namespace, install_type="new"):
#     namespace = Namespace(chart_name=chart_name, chart_repo_url=chart_repo_url, namespace=namespace,
#                           install_type=install_type)
#     db.add(namespace)
#     db.commit()
#     db.refresh(namespace)
#     return namespace

def create_namespace_record(chart_name, chart_repo_url, namespace):
    existing_namespace = db.query(Deployment).filter_by(namespace=namespace).filter_by(install_type="new").first()
    ns = []
    if existing_namespace:
        exist_namespace = Deployment(chart_name=chart_name,
                                     chart_repo_url=chart_repo_url,
                                     namespace=namespace,
                                     install_type="upgrade")
        ns.append(exist_namespace)
        db.add(exist_namespace)
        db.commit()
        db.refresh(exist_namespace)
    else:
        new_namespace = Deployment(chart_name=chart_name,
                                   chart_repo_url=chart_repo_url,
                                   namespace=namespace,
                                   install_type="new")
        ns.append(new_namespace)
        db.add(new_namespace)
        db.commit()
        db.refresh(new_namespace)
    return ns


def delete_namespace_record(namespace):
    db.query(Deployment).filter_by(namespace=namespace).delete()
    db.commit()


def get_deployments_db():
    namespaces = []
    result = session.query(Deployment).all()
    for deployment in result:
        namespaces.append(
            {"namespace": deployment.namespace, "chart_name": deployment.chart_name,
             "chart_repo_url": deployment.chart_repo_url, "created_at": deployment.created_at})
    return namespaces


def delete_all_namespaces_from_db():
    session.query(Deployment).delete()
    session.commit()


def get_all_namespaces_from_db():
    namespaces = []
    result = session.query(Deployment.namespace).all()
    for namespace in result:
        namespaces.append(namespace[0])
    session.close()
    return namespaces
