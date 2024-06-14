import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Load environment variables
psq_pass = os.getenv("POSTGRES_PASSWORD")
db_name = "k8s_api_platform"
db_user = "postgres"
db_host = "postgres-postgresql"
db_port = 5432

# Define the initial database URL for connecting to the default postgres database
DATABASE_URL = f'postgresql://{db_user}:{psq_pass}@{db_host}:{db_port}/postgres'

# Create the database engine for the initial connection
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()


def create_database_if_not_exists():
    with engine.connect() as connection:
        connection.execute(text(f"CREATE DATABASE {db_name}"))


# Create the actual database URL for the application
APPLICATION_DATABASE_URL = f'postgresql://{db_user}:{psq_pass}@{db_host}:{db_port}/{db_name}'

# Create the database engine for the application
app_engine = create_engine(APPLICATION_DATABASE_URL)

# Create a configured "Session" class for the application
AppSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=app_engine)


# Dependency for database sessions
def get_db():
    db = AppSessionLocal()
    try:
        yield db
    finally:
        db.close()
