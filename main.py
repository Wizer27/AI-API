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