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
    

    
