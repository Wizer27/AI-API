import streamlit as st
import numpy
import requests
import hashlib
import hmac
import time
import json

API_URL = "http:0.0.0.0:8080"
json_path_secrets = "/Users/ivan/AI-API/data/secrets.json"




def generate_siganture(data:dict) -> str:
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


def register_api(username:str,psw:str):
    headers = {
        "X-Signature":""
    }