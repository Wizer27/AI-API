from sqlalchemy import text,select
from sql_cli import sync_engine
from models import metadata_obj,users_table
from security.hash_psw import hash_password
import uuid


def create_tables():
    metadata_obj.create_all(sync_engine)

def is_user_exists(username:str) -> bool:
    with sync_engine.connect() as conn:
        stmt = select(text("COUNT(1)")).where(users_table.c.username == username)
        res = conn.execute(stmt)
        count = res.scalar()
        return count > 0 if count else False



def register_new_user(username:str,hash_psw:str) -> bool:
    if is_user_exists(username):
        return False
    with sync_engine.connect() as conn:
        try:
            stmt = users_table.insert(). values(
                username = username,
                hash_psw = hash_password(hash_psw)
            )
            conn.execute(stmt)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error : {e}")
def login(username:str,psw:str) -> bool:
    if not is_user_exists(username):
        return False
    with sync_engine.connect() as conn:
        try:
            stmt = select(users_table.c.hash_psw).where(users_table.c.username == username)
            res = conn.execute(stmt)
            user_data = res.fetchone()
            if not user_data:
                print("DATA NOT FOUND")
                return False
            return user_data[0] == hash_password(psw)    
        except Exception as e:
            print(f"Error : {e}")
            return False  

def add_chat_to_user(username:str,chat_data:dict) -> bool:
    if not is_user_exists(username):
        return False
    with sync_engine.connect() as conn:
        try:
            stmt = select(users_table.c.chats).where(users_table.c.username == username)
            current_chats = conn.scalar(stmt)
            if current_chats is None:
                current_chats = []
            update = current_chats + [chat_data]
            update_stmt = users_table.update().where(users_table.c.username == username).values(chats = update)
            conn.execute(update_stmt)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error : {e}")
            return False


def debug():
    print(register_new_user("us","1"))
    print("-----------")
    print(login("us","1")) 
print(add_chat_to_user(
    username = "us",
    chat_data={
        "id":str(uuid.uuid4()),
        "messages":[]
    }
))

     