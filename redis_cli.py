import redis



class RedisClient():
    def __init__(self):
        self.redis = redis.Redis(host = "0.0.0.0",port = 8090)
        self.redis.ping()
    def register(self,username:str,hash_psw:str) -> bool:
        if self.redis.exists(username):
            return False
        self.redis.set(username,hash_psw)
        return True
    def login(self,username:str,psw:str) -> bool:
        if not self.redis.exists(username):
            return True
        return str(self.redis.get(username)) == psw
     
