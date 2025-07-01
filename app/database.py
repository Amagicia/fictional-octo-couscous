# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://location_1698_user:Scmgt1Keu8Y4SgFsoTM0OVG6PKAUg1Hu@dpg-d1fbfsfgi27c73ckorkg-a/location_1698"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

