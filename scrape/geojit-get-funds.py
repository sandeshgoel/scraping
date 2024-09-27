import requests
import os
import json
from datetime import date, timedelta
import argparse
import time
import sys
import re
from bs4 import BeautifulSoup
import xlsxwriter
from xlsxwriter.utility import * #xl_rowcol_to_cell

import configparser

config = configparser.ConfigParser()
config.read('config.ini')
#print(config.sections())

geojit = config['geojit']
username = geojit['username']
password = geojit['password'] 
fullname = geojit['fullname'] 
PAN = geojit['PAN']

data = config['data']
basegeojit = data['basegeojit']

print(username, fullname, PAN, basegeojit)

now = time.time()
nowstr = time.strftime('%Y-%m-%d_%H-%M-UTC', time.gmtime(now))

nowpr = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(now))
print("Current time:", nowpr)

def url_get(url):
    print("\nGETTING ...", url)
    r = s.get(url)
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
        #sys.exit(1)
    return r

# initialize session
s = requests.session()

# open login page
url = 'https://flip.geojit.net/faces/lite/auth/login.jsp'
r = url_get(url)

soup = BeautifulSoup(r.content, "html.parser")

samples = soup.find_all("input", id="loginform:userText")
if samples == []:
    print("Login id input box not found")
    sys.exit(1)
samples = soup.find_all("input", id="loginform:PassText")
if samples == []:
    print("Password input box not found")
    sys.exit(1)
samples = soup.find_all("input", id="j_id_id17:javax.faces.ViewState:0")
if samples == []:
    print("javax.faces.ViewState input box not found")
    sys.exit(1)
jstate = samples[0]['value']
#print("javax.faces.ViewState =", jstate)

# Logging in
url = 'https://flip.geojit.net/faces/lite/auth/login.jsp'
pl = {'loginform':'loginform', 
      'loginform:userText': username, 
      'loginform:PassText':password,
      'loginform:source':'lite',
      'loginform:reqType':'0',
      'loginform:button1':'Login',
      'javax.faces.ViewState':jstate
     }
r = url_post(url, pl)

soup = BeautifulSoup(r.content, "html.parser")
#samples = soup.find_all("input")
#for x in samples: print(x['type'], x.get('id','noID'), x['name'], x.get('value','noValue'))

samples = soup.find_all("input", id="j_id_id27:javax.faces.ViewState:0")
if samples == []:
    print("javax.faces.ViewState input box not found")
    sys.exit(1)
jstate = samples[0]['value']
#print("javax.faces.ViewState =", jstate)

script = soup.find("script")
#print(type(script))
#print(script.contents)
text = script.contents[0]
pattern = username + '\d+'
#print(pattern)
match = re.search(pattern, text, re.I)
skey = match.group()
#print("Session key =", skey)

# Logging in
url = 'https://flip.geojit.net/faces/lite/auth/FlipSecureCode.jsp'
pl = {'flipsecure':'flipsecure',
      'flipsecure:secureGroup':'2', 
      'flipsecure:TfaText':PAN,
      'flipsecure:j_id_id193':'',
      'flipsecure:usercode':username,
      'flipsecure:sessionkey':skey,
      'flipsecure:source':'lite',
      'flipsecure:pass':password,
      'flipsecure:button1':'Login',
      'javax.faces.ViewState':jstate
     }
r = url_post(url, pl)

#soup = BeautifulSoup(r.content, "html.parser")
#links = soup.find_all("a")
#for link in links:
#    if 'Portfolio' in link.text: 
#        pfurl = link['href']
#        print("***** FOUND IT ******", pfurl)
#url = 'https://flip.geojit.net/faces/lite/common/' + pfurl

# Get portfolio
url = 'https://flip.geojit.net/faces/lite/reports/StockInHand.jsp'
r = url_get(url)

soup = BeautifulSoup(r.content, "html.parser")
table = soup.find("table", {'class':"dataTable"})
if len(table) == 0:
    print(r.content)
    print("Table not found")
    sys.exit(1)

dtable = []
dtable.append([header.text for header in table.find_all('th')])
rows = table.find_all('tr')
for row in rows:
    dtable.append([val.text for val in row.find_all('td')])

#print("\nWriting %d rows ..." % len(dtable))

# Generate fund excel
fname = basegeojit+nowstr+'.xls'
wb = xlsxwriter.Workbook(fname)
ws = wb.add_worksheet('Portfolio')
row = 0
for data in dtable:
    if data == []: continue
    ws.write_row(row, 0, data[1:])
    row += 1
wb.close()    

print("\nWritten %d rows to file %s" % (len(dtable),fname))
print('-------------------------------------------------------')

