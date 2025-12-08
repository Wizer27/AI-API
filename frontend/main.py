import streamlit as st
import numpy
import requests
import hashlib
import hmac
import time
import json

API_URL = "http:0.0.0.0:8080"
json_path_secrets = "/Users/ivan/AI-API/data/secrets.json"

def get_siganture() -> str:
    try:
        with open(json_path_secrets,"r") as file:
            data = json.load(file)
        return data["signature"]
    except KeyError:
        raise KeyError("Key not Found")


def generate_siganture(data:dict) -> str:
    KEY = get_siganture()
    data_to_ver = data.copy()
    data_to_ver.pop("signature",None)
    data_str = json.dumps(data_to_ver, sort_keys=True, separators=(',', ':'))
    expected_signature = hmac.new(KEY.encode(), data_str.encode(), hashlib.sha256).hexdigest()
    return str(expected_signature)


def hash_password(psw:str) -> str:
    byt = psw.encode("utf-8")
    return str(hashlib.sha256(byt).hexdigest())

def register_user(username, password):
    if 'users' not in st.session_state:
        st.session_state.users = {}
    st.session_state.users[username] = password

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'show_register' not in st.session_state:
    st.session_state.show_register = False 
if 'username' not in st.session_state:
    st.session_state.username = ""


def register_api(username:str,psw:str) -> bool:
    data = {
       "username":username,
       "hash_psw":hash_password(psw)
    }
    headers = {
        "X-Signature":generate_siganture(data),
        "X-Timestamp":str(int(time.time()))
    }
    res  = requests.post(f"{API_URL}/register",json = data,headers = headers)
    print(f"Status code : {res.status_code}")
    print(f"Json : {res.json()}")
    print(f"Text : {res.text}")
    return res.status_code == 200
def login(username:str,psw:str):
    data = {
       "username":username,
       "hash_psw":hash_password(psw)
    }
    headers = {
        "X-Signature":generate_siganture(data),
        "X-Timestamp":str(int(time.time()))
    }
    res  = requests.post(f"{API_URL}/login",json = data,headers = headers)
    print(f"Status code : {res.status_code}")
    print(f"Json : {res.json()}")
    print(f"Text : {res.text}")
    return res.status_code == 200