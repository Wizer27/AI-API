from sqlalchemy import text,select
from database.sql_cli import sync_engine
from database.models import metadata_obj,users_table
from database.security.hash_psw import hash_password
import uuid
from typing import Optional,List


def create_tables():
    metadata_obj.create_all(sync_engine)

def is_user_exists(username:str):
    with sync_engine.connect() as conn:
        try:
            stmt = select(users_table.c.username).where(users_table.c.username == username)
            res = conn.execute(stmt)
            return len(res.fetchall()) != 0
        except Exception as e:
            print(f"Error : {e}")
            raise Exception(f"Error : {e}")



def register_new_user(username:str,hash_psw:str) -> bool:
    if is_user_exists(username):
        return False
    with sync_engine.connect() as conn:
        try:
            stmt = users_table.insert().values(
                username = username,
                hash_psw = hash_psw
            )
            conn.execute(stmt)
            conn.commit()
            return True
        except Exception as e:
            print(f"Error : {e}")
            return False
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
            return user_data[0] == psw 
        except Exception as e:
            print(f"Error : {e}")
            return False  

def create_chat(username:str) -> bool:
    if not is_user_exists(username):
        return False
    chat_data = {
        "id":str(uuid.uuid4()),
        "messages":[]
    }
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

def get_user_chats(username:str):
    if not is_user_exists(username):
        print("User not found")
        raise KeyError("User not found")       
    with sync_engine.connect() as conn:
        try:
            stmt = select(users_table.c.chats).where(users_table.c.username == username)
            cur_chats = conn.scalar(stmt)
            return cur_chats
        except Exception as e:
            print(f"Error : {e}")
            raise Exception(f"Error : {e}")    
def send_message(username:str,chat_id:str,role:str,message:str,files:Optional[List[str]]):
    if not is_user_exists(username):
        print(f"User not found")
        raise KeyError("User not found") 
    ind = False
    with sync_engine.connect() as conn:
        try:
            user_chats = get_user_chats(username)
            for chat in user_chats:
                if chat["id"] == chat_id:
                    chat["messages"].append({
                        "role":role,
                        "message":message,
                        "id":str(uuid.uuid4()),
                        "files":files if files is not None else [] 
                    })
                    ind = True
            if ind:
                update_stmt = users_table.update().where(users_table.c.username == username).values(chats = user_chats)
                conn.execute(update_stmt)
                conn.commit()
        except Exception as e:
            raise Exception(f"Error : {e}") 

def delete_chat(username:str,chat_id:str):
    if not is_user_exists(username):
        print("User not found")
        raise KeyError("User not found")
    try:
       with sync_engine.connect() as conn:
            users_chats = get_user_chats(username)
            for chat in users_chats:
               if chat["id"] == chat_id:
                   ind = users_chats.index(chat)
                   users_chats.pop(ind)
            update_stmt = users_table.update().where(users_table.c.username == username).values(chats = users_chats)
            conn.execute(update_stmt)
            conn.commit()
    except Exception as e:
        print(f"Error : {e}")
        raise Exception(f"Error : {e}")           

def get_chat_messages(username:str,chat_id:str) -> List:
    if not is_user_exists(username):
        raise KeyError("User not found")
    with sync_engine.connect() as conn:
        try:
            chats = get_user_chats(username)
            for chat in chats:
                if chat["id"] == chat_id:
                    return chat["messages"]
            return []    
        except Exception as e:
            raise Exception(f"Error : {e}")
    
def get_user_all_messages(username:str) -> Optional[List[str]]:
    if not is_user_exists(username):
        return []
    with sync_engine.connect() as conn:
        try:
            stmt = select(users_table.c.chats).where(users_table.c.username == username)
            res = conn.execute(stmt)
            data = res.fetchone()[0]
            messages = []
            for chat in data:
                for message in chat["messages"]:
                    messages.append(message["message"])
            return messages        
        except Exception as e:
            print(f"Error : {e}")
            return []

def debug():
    print(register_new_user("us1","2"))
    print("-----------")
    print(login("us","1")) 



     