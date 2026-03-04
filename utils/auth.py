import hashlib
import jwt
from datetime import datetime, timedelta
from fastapi import Header, HTTPException

SECRET = "reverselens-change-this-key-in-prod"
ALG = "HS256"
EXP_HOURS = 24

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def check_pw(pw, hashed):
    return hash_pw(pw) == hashed

def create_token(user_id, username):
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=EXP_HOURS)
    }
    return jwt.encode(payload, SECRET, algorithm=ALG)

def decode_token(token):
    try:
        return jwt.decode(token, SECRET, algorithms=[ALG])
    except jwt.ExpiredSignatureError:
        return None
    except:
        return None

def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Token kerak")
    token = authorization.split(" ")[1]
    data = decode_token(token)
    if not data:
        raise HTTPException(401, "Token eskirgan yoki noto'g'ri")
    return data
