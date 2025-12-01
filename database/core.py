from sqlalchemy import text,select
from sql_cli import sync_engine
from models import metadata_obj,users_table


def create_tables():
    #metadata_obj.drop_all(sync_engine)
    metadata_obj.create_all(sync_engine)

def is_user_exists(username:str) -> bool:
    with sync_engine.connect() as conn:
        stmt = select(text("COUNT(0)")).where(users_table.c.username == username)
        res = conn.execute(stmt)
        print(res.fetchone())
        return res.fetchone() is not None



def register_new_user(username:str,hash_psw:str):
    with sync_engine.connect() as conn:
        stmt = "INSERT"
print(is_user_exists(""))        