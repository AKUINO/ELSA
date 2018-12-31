import binascii
import datetime
import fcntl
import hashlib
import math
import smtplib
import socket
import struct
import time
import traceback
import urllib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GMAIL_USER = u'christophe.dupriez@guest.uliege.be' #u'akuino6002@gmail.com'
GMAIL_PASS = u'vjdQ5631' #u'My_Password6002'
SMTP_SERVER = u'smtp.ulg.ac.be' #'u'smtp.gmail.com'
SMTP_PORT = 587
csvDir = "../ELSAcsv/csv/"

datetimeformat = "%Y-%m-%d %H:%M:%S"
shortformat = "%y%m%d"

# Returns the value of the key if it exists in the string, None otherwise
# Exemple : string = "?abc=123&def=456", key = "def", will return 456
def parse_url_query_string(string, key):
    string = string.split('&')
    for item in string:
        item = item.split('=')
        if item[0] == key:
            return urllib.unquote(item[1]).decode('UTF-8')
    return None

def get_timestamp():
    now = time.time()
    now = math.floor(float(now))
    now = int(now)
    return now

def str_float(v):
    if v:
        try:
            return float(v)
        except:
            return 0.0
    else:
        return 0.0

def encrypt(password, salt):
    sha = hashlib.pbkdf2_hmac('sha256', password, salt, 126425)
    return binascii.hexlify(sha)


def send_email(hardconfig, recipient, subject, text):
  print "Mail to "+recipient+" about "+subject+" : "+text
  try:
    smtpserver = smtplib.SMTP(hardconfig.mail_server, hardconfig.mail_port)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo
    smtpserver.login(hardconfig.mail_user, hardconfig.mail_password)
    header = u'To:' + recipient + u'\n' + u'From: ' + hardconfig.mail_user
    header = header + '\n' + u'Subject:' + subject + u'\n'

    msg = MIMEMultipart('alternative')
    msg.set_charset('utf8')
    msg['From'] = hardconfig.mail_user
    msg['To'] = recipient
    msg['Subject'] = Header(
        subject.encode('utf-8'),
        'UTF-8'
    ).encode()

    _attach = MIMEText(text.encode('utf-8'), 'plain', 'UTF-8')
    msg.attach(_attach)
    print msg.as_string()

    smtpserver.sendmail(hardconfig.mail_user, recipient, msg.as_string())
    smtpserver.close()
    print "DONE"
    return True
  except:
    traceback.print_exc()
    return False

def send_sms(hardconfig, recipient, subject, text):
    print "Fail to SMS to "+recipient+" about "+subject+" : "+text
    return False

def timestamp_to_date(now, format=datetimeformat):
    return datetime.datetime.fromtimestamp(int(now)).strftime(format)


def timestamp_to_time(now):
    return str(datetime.timedelta(seconds=now))

def timestamp_to_ISO(start):
    if not start:
        return ""
    a_date = datetime.datetime.fromtimestamp(float(start))
    return a_date.isoformat(sep=' ')

def get_time():
    now = int(time.time())
    return datetime.datetime.fromtimestamp(now).strftime(datetimeformat)

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])


def string_to_date(input):
    tmp = None
    try:
        tmp = datetime.datetime.strptime(input, datetimeformat)
    except:  # old format ?
        try:
            tmp = datetime.datetime.strptime(input, "%H:%M:%S  -  %d/%m/%y")
        except: # EPOCH timestamp?
            tmp = datetime.datetime.fromtimestamp(int(input))
    return tmp

def date_to_timestamp(input):
    tmp = string_to_date(input)
    if tmp:
        return (tmp - datetime.datetime(1970, 1, 1)).total_seconds()
    return 0

def date_to_ISO(date):
    if date and date != '0':
        try:
            tmp = datetime.datetime.strptime(date, datetimeformat)
        except:  # old format ?
            try:
                tmp = datetime.datetime.strptime(
                    date, "%H:%M:%S  -  %d/%m/%y")
            except: # EPOCH timestamp?
                tmp = datetime.datetime.fromtimestamp(int(date))
        return tmp.isoformat(sep=' ')
    else:
        return ''


def now():
    return unicode(datetime.datetime.now().strftime(datetimeformat))

def shortNow():
    return unicode(datetime.datetime.now().strftime(shortformat))

def shorten_time(longTime, prevTime):
    if not longTime:
        return ""
    elif longTime == prevTime:
        return ' " " " '
    elif longTime[:11] == prevTime[:11]:
        return longTime[11:]
    return longTime
