import hashlib

def hash_token(token_str):
    return hashlib.sha256(token_str.encode()).hexdigest()