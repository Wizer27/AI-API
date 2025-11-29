from fastapi import FastAPI,Reuqets,Depends,HTTPException,Header
import uvicorn
import hmac
import hashlib
import json
import requests
import time
import uuid
from secrets import compare_digest
from pydantic import BaseModel,Field


secrets_file = "data/secrets.json"
users_file = "data/users.json"
chats_file = "data/chats.json"

def get_secrets_keys(argument:str) -> str:
    try:
        with open(secrets_file,"r") as file:
            data = json.load(file)
        return data[argument]
    except Exception as e:
        raise KeyError(f"Error : {e}")
    
 


def verify_signature(data:dict,rec_signature) -> bool:
    if time.time() - data.get('timestamp',0) > 300:
        return False
    KEY = get_secrets_keys("signature")
    data_to_verify = data.copy()
    data_to_verify.pop("signature",None)
    data_str = json.dumps(data_to_verify,sort_keys = True,separators = (',',':'))
    expected = hmac.new(KEY.encode(),data_str.encode(),hashlib.sha256).hexdigest()
    return hmac.compare_digest(rec_signature,expected)
def try_except_decorator(func):
    def check(*args,**kwargs):
        try:
            func()
        except Exception as e:
            raise Exception(e)    
    return check    

@try_except_decorator
def write_default_chats(username:str):
    try:
        with open(chats_file,"r") as file:
            data = json.load(file)
        data.append({
            "username":username,
            "chats":[]
        })    
        with open(chats_file,"w") as file:
            json.dump(data,file)
    except Exception as e:
        raise KeyError(f"Error : {e}")

@try_except_decorator
def is_user_exists(username:str) -> bool:
    try:
        with open(users_file,"r") as file:
            data = json.load(file)
        usernames = []
        for key in data.keys():
            usernames.append(key)
        l = 0
        r = len(usernames) - 1
        usernames = sorted(usernames)
        while l <= r:
            mid = (l + r) // 2
            if usernames[mid] < username:
                l = mid + 1
            elif usernames[mid] > username:
                r = mid - 1
            else:
                return True
        return False            
    except Exception as e:
        raise Exception(e)

app = FastAPI()
@app.get("/")
async def main():
    return "AI API"

class RegisterLogin(BaseModel):
    username:str
    hash_psw:str
@app.post("/register")
async def register(req:RegisterLogin,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = 401,detail = "Invalid signature")
    try:
        if is_user_exists(req.username):
            raise HTTPException(status_code = 400,detail = "Username is already taken")
        else:
            with open(users_file,"r") as file:
                data = json.load(file)
            data[req.username] = req.hash_psw
            with open(users_file,"w") as file:
                json.dump(data,file)
            #default data
            write_default_chats(req.username)    
    except Exception as e:
        raise HTTPException(status_code = 400,detail = e) 
@app.post("/login")
async def login(req:RegisterLogin,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = 401,detail = "Invalid signature")
    try:
        if not is_user_exists(req.username):
            raise HTTPException(status_code = 404,detail = "User not found")
        with open(users_file,"r") as file:
            data = json.load(file)
        return data[req.username] == req.hash_psw    
    except Exception as e:
        raise HTTPException(status_code = 400,detail = f"Error : {e}")    
class CreateNewChat(BaseModel):
    username:str

@app.post("/create/new/chat")
async def create_new_chat(req:CreateNewChat,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = 401,detail = "Invalid signature")
    try:
        with open(chats_file,"r") as file:
            data = json.load(file)
        for user in data:
            if user["username"] == req.username:
                user["chats"].append({
                    "id":str(uuid.uuid4()),
                    "messages":[]
                })    
                with open(chats_file,"w") as file:
                    json.dump(data,file)
    except Exception as e:
        raise HTTPException(status_code = 400 ,detail = f"Error : {e}")
