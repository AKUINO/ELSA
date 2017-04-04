import time
import math
import hashlib
import binascii
import smtplib
import datetime

GMAIL_USER = 'akuino6002@gmail.com'
GMAIL_PASS = 'My_Password6002'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

def get_timestamp():
    now = time.time()
    now = math.floor(float(now))
    now = int(now)
    return now

def encrypt(password,salt):
    sha = hashlib.pbkdf2_hmac('sha256', password, salt, 126425)
    return binascii.hexlify(sha)

def send_email(recipient, subject, text):
    smtpserver = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo
    smtpserver.login(GMAIL_USER, GMAIL_PASS)
    header = 'To:' + recipient + '\n' + 'From: ' + GMAIL_USER
    header = header + '\n' + 'Subject:' + subject + '\n'
    msg = header + '\n' + text + ' \n\n'
    smtpserver.sendmail(GMAIL_USER, recipient, msg)
    smtpserver.close()

def timestamp_to_date(now):
    return datetime.datetime.fromtimestamp(int(now)).strftime("%H:%M:%S  -  %d/%m/%y")
    
def get_time(now):
    now = int(time.time())
    return datetime.datetime.fromtimestamp(now).strftime("%H:%M:%S  -  %d/%m/%y")
