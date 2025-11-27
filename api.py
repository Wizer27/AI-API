from fastapi import FastAPI,Reuqets,Depends,HTTPException,Header
import uvicorn
import hmac
import hashlib
import json
import requests
import time
from secrets import compare_digest
from pydantic import BaseModel,Field


secrets_file = "data/secrets.json"

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



app = FastAPI()
@app.get("/")
async def main():
    return "AI API"
