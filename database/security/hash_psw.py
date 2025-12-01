import hashlib
import hmac


def hash_password(psw:str) -> str:
    byt = psw.encode("utf-8")
    return str(hashlib.sha256(byt).hexdigest())
