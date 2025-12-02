from fastapi import FastAPI,Request,Depends,HTTPException,Header,status
import uvicorn
import hmac
import hashlib
import json
import requests
import time
import uuid
import os
from dotenv import load_dotenv
from secrets import compare_digest
from pydantic import BaseModel,Field
from typing import Optional,List
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from database.core import register_new_user,login,create_chat,get_user_chats,send_message,delete_chat,get_chat_messages



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
async def safe_get(req:Request):
    try:
        api = req.headers.get("X-API-KEY")
        if not api or hmac.compare_digest(api,get_secrets_keys("api")):
            raise HTTPException(status_code = 401,detail = "Invalid API key")
    except Exception as e:
        raise HTTPException(status_code = 401,detail = "Invalid api key")



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

limiter = Limiter(key_func = get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.get("/")
@limiter.limit("900/minute")
async def main(request:Request):
    return "AI API"

class RegisterLogin(BaseModel):
    username:str
    hash_psw:str
@app.post("/register")
@limiter.limit("900/minute")
async def register(request:Request,req:RegisterLogin,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = 401,detail = "Invalid signature")
    try:
        res = register_new_user(req.username,req.hash_psw)
        if res:
            create_chat(req.username)
        return res    
    except Exception as e:
        raise HTTPException(status_code = 400,detail = e) 
@app.post("/login")
@limiter.limit("900/minute")
async def login_api(request:Request,req:RegisterLogin,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = 401,detail = "Invalid signature")
    try:
        res = login(req.username,req.hash_psw)
        return res
    except Exception as e:
        raise HTTPException(status_code = 400,detail = f"Error : {e}")    
class CreateNewChat(BaseModel):
    username:str

@app.post("/create/new/chat")
@limiter.limit("900/minute")
async def create_new_chat(request:Request,req:CreateNewChat,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = 401,detail = "Invalid signature")
    try:
        create_chat(req.username)
    except Exception as e:
        raise HTTPException(status_code = 400 ,detail = f"Error : {e}")
class DeleteChat(BaseModel):
    username:str
    chat_id:str
@app.post("/delete/chat")
@limiter.limit("900/minute")
async def delete_chat_api(request:Request,req:DeleteChat,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = 401,detail = "Invalid signature") 
    try:
       res = delete_chat(req.username,req.chat_id)
    except Exception as e:
        raise HTTPException(status_code = 400,detail = f"Error : {e}")       

@app.get("/get/{username}/chats",dependencies=[Depends(safe_get)])
@limiter.limit("900/minute")
async def get_user_chats_api(request:Request,username:str):
    try:
        return get_user_chats(username)    
    except Exception as e:
        raise HTTPException(status_code = 400,detail = f"Error : {e}")

class SendMessage(BaseModel):
    username:str
    chat_id:str
    message:str
    files:Optional[List[str]]
    role:str
@app.post("/send/message")    
@limiter.limit("900/minute")
async def send_message_api(request:Request,req:SendMessage,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = 401,detail = "Invalid signature")
    try:
        if req.role != "ai" and req.role != "user":
            raise HTTPException(status_code = 400,detail = "Invalid role")
        send_message(req.username,req.chat_id,req.role,req.message,req.files)
    except Exception as e:
        raise HTTPException(status_code = 400,detail = f"Error : {e}")

class GetChatMessages(BaseModel):
    username:str
    chat_id:str
@app.post("/get/chat/messages")
@limiter.limit("900/minute")
async def get_chat_messages_api(request:Request,req:GetChatMessages,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = 401,detail = "Invalid signature")
    try:
        return get_chat_messages(req.username,req.chat_id)
    except Exception as e:
        raise HTTPException(status_code = 400,detail = f"Error : {e}")
    


load_dotenv()
   

    
if __name__ == "__main__":
    uvicorn.run(app,host = "0.0.0.0",port = 8080)
