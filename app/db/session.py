from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL
from app.core.config import settings

# create a postgres sql connection from setting  which is created  core/config
#psycopg is use  for  communicate with DB
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=settings.DB_USER,
    password=settings.DB_PASSWORD,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
)
# Engine is managed connection in the DB
engine = create_engine(DATABASE_URL)

# DB session create which helps in read create update and delete process
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)






