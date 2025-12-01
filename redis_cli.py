import redis
from typing import Optional,List
import json




class RedisLoginClient():
    def __init__(self):
        self.redis = redis.Redis(host = "0.0.0.0",db = 0,port = 8090)
        self.redis.ping()
    def register(self,username:str,hash_psw:str) -> bool:
        if self.redis.exists(username):
            return False
        self.redis.set(username,hash_psw)
        return True
    def is_user_exists(self,username:str) -> bool:
        return self.redis.exists(username)
    def login(self,username:str,psw:str) -> bool:
        if not self.redis.exists(username):
            return True
        return str(self.redis.get(username)) == psw
login_redis = RedisLoginClient()

class RedisChats():
    def __init__(self):
        self.redis = redis.Redis(host = "0.0.0.0",db = 1,port = 8091)
        self.redis.ping()
    def add_list(self,username:str,data):
        if not login_redis.is_user_exists(username):
            raise KeyError("User not found")
        self.redis.rpush(username,json.dumps(data))
    def get_user_data(self,username:str):
        data = self.redis.lrange(username,0,-1)
        return [json.loads(item) for item in data]



    
     
