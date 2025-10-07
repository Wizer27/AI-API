from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from pydantic import BaseModel,Field
import json
import threading
import socket
from typing import Union,Literal,List,Optional
import random
from pydantic.types import StrictStr
from pydantic_core.core_schema import str_schema
import uuid
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from olama import Client
import redis
import uvicorn
import time
import hmac
import uuid
import hashlib



def get_key():
    with open("secrets.json","r") as file:
        data = json.load(file)
    return data["key"]    

def verify_signature(data:dict,rec_signature) -> bool:
    if time.time() - data.get('timestamp',0) > 300:
        return False
    KEY = "test"
    data_to_verify = data.copy()
    data_to_verify.pop("signature",None)
    data_str = json.dumps(data_to_verify,sort_keys = True,separators = (',',':'))
    expected = hmac.new(KEY.encode(),data_str.encode(),hashlib.sha256).hexdigest()
    return hmac.compare_digest(rec_signature,expected)



app = FastAPI()


@app.get("/")
async def main():
    return "AI URIST API"


class Login(BaseModel):
    username:str
    passw:str

@app.post("/login")
async def login(request:Login) -> bool:
    with open("users.json","r") as file:
        data = json.load(file)

    if request.username in data:
        return data[request.username] == request.passw
    raise HTTPException(status_code=404,detail="User not found")
    
async def register(request:Login):
    with open("users.json","r") as file:
        data = json.load(file)
    if request.username not in data:
        data[request.username] = request.passw
        with open("users.json","w") as file:
            json.dump(data,file)
        ### default messages
        try:
            with open("chats.json","r") as file:
                mes = json.load(file)
            mes.append({
                "username":request.username,
                "chats":[]
            }) 
            with open("chats.json","w") as file:
                json.dump(mes,file)  
        except Exception as e:
            raise HTTPException(status_code=400,detail= f"Exception: {e}")         
        
    else:
        raise HTTPException(status_code=400,detail="User alredy exists")
    

class GetResponse(BaseModel):
    search:str
    username:str
    chat_id:str

AI = Client()
@app.post("/AI/answer")
async def answer(request:GetResponse):
    with open("request.json","r") as file:
        data = json.load(file)
    done = False   
    repsonse = AI.generate(request.search)
    try:    
        for user in data:
            if user["username"] == request.username:
                user["requests"].append(
                    {
                        "user_question":request.search,
                        "ai_response":repsonse
                    }
                )
                done = True
        if done:        
            with open("requests.json","w") as file:
                json.dump(data,file)   
            return repsonse         
    except Exception as e:
        raise HTTPException(status_code = 400,detail=f"Exception while try: {e}")   

class CreateNewChat(BaseModel):
    username:str
    id:str = Field(default_factory=lambda: str(uuid.uuid4()))
@app.post("/create/new/chat") 
async def create_new_chat(request:CreateNewChat):
    with open("chats.json","r") as file:
        data = json.load(file)
    done = False    
    for user in data:
        if user["username"] == request.username:
            user["chats"].append({
                "messages" : [],
                "id":request.id
            })   
            done = True
    if done:
        with open("chats.json","w") as file:
            json.dump(data,file) 

class Delete_Chat(BaseModel):
    username:str
    id:str            
@app.post("/delete/chat")
async def delete_chat(request:Delete_Chat):
    with open("chats.json","r") as file:
        data = json.load(file)
    for user in data:
        if user["username"] == request.username:
            for chat in user["chats"]:
                if chat["id"] == request.id:
                    ind = user["chats"].index(chat)
                    user["chats"].pop(ind)
                    with open("chats.json","w") as file:
                        json.dump(data,file)
                        return
    raise HTTPException(status_code=400,detail="User not found")                


class AddNewMessage(BaseModel):
    role:str
    message:str
    id:str
    username:str
    id_message:str = Field(default_factory=lambda: str(uuid.uuid4()))

@app.post("/send/message")
async def send(request:AddNewMessage):
    with open("chats.json","r") as file:
        chats = json.load(file)
    found = False    
    for user in chats:
        if user["username"] == request.username:
            for chat in user["chats"]:
                if chat["id"] == request.id:
                    found = True
                    chat["messages"].append({
                        "role":request.role,
                        "message":request.message,
                        "id":request.id_message
                    })
    if found:
        with open("chats.json","w") as file:
            json.dump(chats,file)
    else:
        raise HTTPException(status_code=400,detail="User not found")                        

class DeleteMessage(BaseModel):
    username:str
    id_chat:str
    id_message:str
    role:str
@app.post("/delete/message")
async def delete_message(request:DeleteMessage):
    with open("chats.json","r") as file:
        chats = json.load(file)
    found = False  
    for user in chats:
        if user["username"] == request.username:
            for chat in user["chats"]:
                if chat["id"] == request.id_chat:
                    for message in chat:
                        if message["id"] == request.id_message:
                            try:
                                index = chat.index(message)
                                chat.pop(index)
                                found = True
                                break
                            except Exception as e:
                                raise HTTPException(status_code=400,detail=f"Something went wrong, error: {e}")    
    if found:
        with open("chats.json","w") as file:
            json.dump(chats,file)
    else:
        raise HTTPException(status_code=400,detail="Error while wring the data")                            
#FIXME write the logic to change the message

async def redis_init_user(username:str) -> bool:
    redis = redis.Redis("localhost",8888,0,decode_response = True)

    if not redis.exists(f"user:{username}"):
        new_user = {
            "chats":json.dumps([])
        }
        redis.hset(f"user:{username}", mapping=new_user)
        return True
    print("User alredy in database")
    return False

class ChangePromt(BaseModel):
    username:str
    message_id:str
    chat_id:str
    new_message:str
@app.post("/user/change/message")
async def change_message(request:ChangePromt):
    try:
        with open("chats.json","r") as file:
            data = json.load(file)
        for user in data:
            if user["username"] == request.username:
                for chat in user["chats"]:
                    if chat["id"] == request.chat_id:
                        for message in chat["messages"]:
                            if message["id"] == request.message_id:
                                if message["role"] == request.username:
                                    message["message"] = request.new_message
                                    with open("chats.json","w") as file:
                                        json.dump(data,file)
                                    return True
        return False                        
    except Exception as e:
        raise HTTPException(status_code=400,detail=f"Error : {e}")       
if __name__ == "__main__":
    uvicorn.run(app,host = "0.0.0.0",port = 8080)
                               
