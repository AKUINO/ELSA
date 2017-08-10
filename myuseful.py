import time
import math
import hashlib
import binascii
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import datetime
import socket
import fcntl
import struct

import unicodecsv

GMAIL_USER = u'akuino6002@gmail.com'
GMAIL_PASS = u'My_Password6002'
SMTP_SERVER = u'smtp.gmail.com'
SMTP_PORT = 587
csvDir = "../ELSAcsv/csv/"

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
    header = u'To:' + recipient + u'\n' + u'From: ' + GMAIL_USER
    header = header + '\n' + u'Subject:' + subject + u'\n'

    msg = MIMEMultipart('alternative')
    msg.set_charset('utf8')
    msg['From'] = GMAIL_USER
    msg['To'] = recipient
    msg['Subject'] = Header(
        subject.encode('utf-8'),
        'UTF-8'
    ).encode()

    _attach = MIMEText(text.encode('utf-8'), 'plain', 'UTF-8')        
    msg.attach(_attach)

    smtpserver.sendmail(GMAIL_USER, recipient, msg.as_string())
    smtpserver.close()

def timestamp_to_date(now,datetimeformat):
    return datetime.datetime.fromtimestamp(int(now)).strftime(datetimeformat)
    
def timestamp_to_time(now):
    return datetime.datetime.fromtimestamp(int(now)).strftime("%H:%M:%S")
    
def get_time(datetimeformat):
    now = int(time.time())
    return datetime.datetime.fromtimestamp(now).strftime(datetimeformat)

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

def date_to_timestamp(date, datetimeformat):
    return int(time.mktime(datetime.datetime.strptime(date, datetimeformat).timetuple()))
    
def date_normalize():
    files = ['A.csv','alarmlogs.csv','Anames.csv','B.csv','Bnames.csv','C.csv','Cnames.csv', 'codes.csv', 'CPEHM.csv','CPEHMnames.csv', 'D.csv', 'E.csv', 'Enames.csv', 'G.csv', 'Gnames.csv', 'halflings.csv', 'language.csv', 'M.csv', 'mess.csv', 'messages.csv', 'Mnames.csv', 'P.csv', 'Pnames.csv', 'relations.csv', 'T.csv', 'U.csv', 'Unames.csv', 'V.csv']
    for e in files :
	fname = csvDir+e
	print fname
	with open(fname, 'r') as csvfile:
	    row =  csvfile.readline()		
	with open(fname) as csvfile:
	    reader = unicodecsv.DictReader(csvfile, delimiter = "\t")
	    with open(fname,'w') as csvfile:
		row = row.split('\t')
		if 'deny' in row:
		    row[row.index('deny')] = 'active'
		for e in row:
		    csvfile.write(e)
		    if not 'user' in e or ('alarmlogs' in fname and 'degree' in e):
			csvfile.write('\t')
		if 'active'in row:
		    row[row.index('active')] = 'deny'
		if 'alarmlog' in fname:
                    row[-1] = u'degree'
                else: 
                    row[-1] = u'user'
		print row
	    with open(fname,"a") as copyfile:
		for elems in reader:
		    elems['begin'] = transform_date(elems['begin']).replace('T',' ')
		    if 'time' in elems.keys():
			if elems['time'] != '' :
			    elems['time'] = transform_date(elems['time']).replace('T',' ')					
		    writer = unicodecsv.DictWriter(copyfile, delimiter = '\t', fieldnames=row, encoding="utf-8")
		    writer.writerow(elems)

def transform_date( date):
    try:
	tmp = datetime.datetime.strptime(date, "%H:%M:%S  -  %d/%m/%y").isoformat()
    except:
	tmp = datetime.datetime.strptime(date, "%d/%m/%Y %H:%M:%S").isoformat()
    return tmp


