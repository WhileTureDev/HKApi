import os
from datetime import datetime

from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlalchemy.orm as _orm

psq_pass = os.getenv("POSTGRES_PASSWORD")
Base = declarative_base()


class Deployment(Base):
    __tablename__ = 'deployments'

    id = Column(Integer, primary_key=True, index=True)
    release_type = Column(String, index=True)
    install_type = Column(String, index=True)
    chart_name = Column(String, index=True)
    chart_repo_url = Column(String, index=True)
    namespace = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    owner = _orm.relationship("User", back_populates="deployments")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    full_name = Column(String)
    email = Column(String)
    password = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    deployments = _orm.relationship("Deployment", back_populates="owner")


# Connect to the database
engine = create_engine(f'postgresql://postgres:{psq_pass}@postgress-postgresql:5432')
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = sessionmaker(bind=engine)
session = Session()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_deployment_record(chart_name, chart_repo_url, namespace):
    existing_namespace = session.query(Deployment).filter_by(namespace=namespace).filter_by(install_type="new").first()
    ns = []
    if existing_namespace:
        exist_namespace = Deployment(chart_name=chart_name,
                                     chart_repo_url=chart_repo_url,
                                     namespace=namespace,
                                     install_type="new",
                                     created_at=datetime.utcnow())
        ns.append(exist_namespace)
        session.add(exist_namespace)
        session.commit()
        session.refresh(exist_namespace)
    else:
        new_namespace = Deployment(chart_name=chart_name,
                                   chart_repo_url=chart_repo_url,
                                   namespace=namespace,
                                   install_type="update",
                                   updated_at=datetime.utcnow())
        ns.append(new_namespace)
        session.add(new_namespace)
        session.commit()
        session.refresh(new_namespace)
    return ns


def delete_namespace_record(namespace):
    session.query(Deployment).filter_by(namespace=namespace).delete()
    session.commit()


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
