import time
import math
import hashlib
import binascii

def get_timestamp():
    now = time.time()
    now = math.floor(float(now))
    now = int(now)
    return now

def encrypt(password,salt):
    sha = hashlib.pbkdf2_hmac('sha256', password, salt, 126425)
    return binascii.hexlify(sha)
