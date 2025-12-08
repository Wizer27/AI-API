import streamlit as st
import numpy
import requests
import hashlib
import hmac
import time
import json

API_URL = "http://0.0.0.0:8080"
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

if not st.session_state.logged_in:
    st.set_page_config(layout="wide")

    
    if st.session_state.show_register:
        st.title("📝 Registration")
        new_username = st.text_input("Username", key="reg_user")
        new_password = st.text_input("Password", type="password", key="reg_pass1")
        confirm_password = st.text_input("Retype the password", type="password", key="reg_pass2")
        
        if st.button("Create an account"):
            if not new_username or not new_password:
                st.error("Fill all the field.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")       
            else:    
                api_answer = register_api(new_username, hash_password(new_password)) 
                if not api_answer:
                    st.error("This username is already taken.")
                else:    
                    st.success("Successfully created an account. Now you can sign in.")
                    st.session_state.show_register = False
                            
        if st.button("← Back to sign in"):
            st.session_state.show_register = False
            st.rerun()
    
    else:
        st.title("🔒 Sign in ")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Sign in"):
            if login(username, hash_password(password)):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Wrong password or username")
                
        if st.button("Sign up"):
            st.session_state.show_register = True
            st.rerun()
    
    st.stop()
st.success("DONE")   
