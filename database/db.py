from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Replace with your Supabase DB URL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres.hagfxtawcqlejisrlato:UHSoUJ0CAdJJLPJv@aws-0-ap-south-1.pooler.supabase.com:5432/postgres"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
