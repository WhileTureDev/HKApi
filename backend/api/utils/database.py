import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Load environment variables
psq_pass = os.getenv("POSTGRES_PASSWORD")
db_name = "k8s_api_platform"
db_user = "postgres"
db_host = "postgres-postgresql"
db_port = 5432

# Define the initial database URL for connecting to the default postgres database
DATABASE_URL = f'postgresql://{db_user}:{psq_pass}@{db_host}:{db_port}/postgres'

# Create the database engine for the initial connection
engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")

# Base class for declarative models
Base = declarative_base()


def create_database_if_not_exists():
    with engine.connect() as connection:
        result = connection.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
        exists = result.scalar()
        if not exists:
            try:
                connection.execute(text(f"CREATE DATABASE {db_name}"))
            except IntegrityError:
                print(f"Database {db_name} already exists.")


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


def create_tables():
    Base.metadata.create_all(bind=app_engine)
