from sqlalchemy import text
from sql_cli import sync_engine
from models import metadata_obj


def create_tables():
    metadata_obj.create_all(sync_engine)

create_tables()