import requests
import os
import json
from datetime import date, timedelta
import argparse
import time
import sys
from bs4 import BeautifulSoup

from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

import configparser

config = configparser.ConfigParser()
config.read('config.ini')
#print(config.sections())

mfu = config['mfu']
#print(mfu['password'])

username = mfu['username']
password = mfu['password'] 
password2 = mfu['password2'] 
canID = mfu['canID'] 
fullname = mfu['fullname'] 
fullname = fullname.replace(' ', '%20')

data = config['data']
basemfu = data['basemfu']

print(username, canID, fullname, basemfu)

now = time.time()
nowstr = time.strftime('%Y-%m-%d_%H-%M-UTC', time.gmtime(now))

nowpr = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(now))
print("Current time:", nowpr)

def url_get(url):
    print("\nGETTING ...", url)
    r = s.get(url, verify=False)
    print("STATUS =", r.status_code)
    if r.status_code != 200:
        print("Request failed")
        sys.exit(1)
    return r

def url_post(url, pl):
    print("\nPOSTING ...", url, pl)
    r = s.post(url, data=pl)
    print("STATUS =", r.status_code)
    if r.status_code != 200:
        print("Request failed")
        sys.exit(1)
    return r

# initialize session
s = requests.session()

# open MFU login page
url = 'https://www.mfuonline.com/'
r = url_get(url)

soup = BeautifulSoup(r.content, "html.parser")
samples = soup.find_all("input", id="loginid")
#print(samples)
if samples == []:
    print("Login id input box not found")
    sys.exit(1)
samples = soup.find_all("input", id="password")
#print(samples)
if samples == []:
    print("Password input box not found")
    sys.exit(1)

# Logging in
url = 'https://www.mfuonline.com/MfUtilityLogin.do'
pl = {'loginid': username, 'password':password}
r = url_post(url, pl)

soup = BeautifulSoup(r.content, "html.parser")
samples = soup.find_all("input", id="txnPassword")
#print(samples)
if samples == []:
    print("Txn Password input box not found")
    sys.exit(1)

url = 'https://www.mfuonline.com/MfUtilityLogin.do'
pl = {'txnPassword':password2}
r = url_post(url, pl)

# Download fund excel
url = ('https://www.mfuonline.com/JasperReportVer2.do?Format=EXCEL&setinRequest=NO&NoOfReport=1&REPORT_1=CANHoldingReport.jasper' +
      '&paging=false&ForwardPage=view&allowFormat=EXCEL&parent=true&viewOnlyFlag=N' +
      '&canNo=(%27' + canID + '%27)&canName=' + fullname + '&zeroHoldingFlag=N')
r = url_post(url, {})
#print(r.content)

fname = basemfu+nowstr+'.xls'
output = open(fname, 'wb')
output.write(r.content)
output.close()
print("\nWritten output to file %s" % fname)
print('-------------------------------------------------------')

