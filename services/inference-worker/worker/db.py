from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from worker.config import settings

engine = create_engine(settings.database_url)
Session = sessionmaker(engine, expire_on_commit=False)
