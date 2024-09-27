from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import pandas as pd 
import time
import sys
import re

import configparser

config = configparser.ConfigParser()
config.read('config.ini')
#print(config.sections())

cm = config['capitalmind']
userid = cm['userid'] 
passwd = cm['passwd'] 

data = config['data']
basecm = data['basecapitalmind']

print(userid, basecm)

now = time.time()
nowstr = time.strftime('%Y-%m-%d_%H-%M-UTC', time.gmtime(now))
todaystr = time.strftime('%Y-%m-%d', time.gmtime(now))

timeout = 10

def exception_quit(browser):
	browser.quit()
	sys.exit(1)

def wait_load(browser, timeout, xpath):
	print("%s: Waiting for %d seconds [%s]" % (time.strftime('%H:%M:%S', time.gmtime(time.time())), timeout, xpath))
	try:
		WebDriverWait(browser, timeout).until(EC.visibility_of_element_located((By.XPATH, xpath)))
	except TimeoutException:
		input('Enter to continue ...')
		print("Timed out waiting for page to load")
		exception_quit(browser)

def load_page(browser, url, xpath):
	browser.get(url)
	print("%s: Loading %s ..." % (time.strftime('%H:%M:%S', time.gmtime(time.time())), url))
	wait_load(browser, timeout, xpath)

# Specifying incognito mode as you launch your browser[OPTIONAL]
option = webdriver.ChromeOptions()
option.add_argument("--incognito")
#option.add_argument("--headless")
option.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Create new Instance of Chrome in incognito mode
service = Service(executable_path='/usr/local/bin/chromedriver')
browser = webdriver.Chrome(service=service, options=option)

# Go to desired website
load_page(browser, "https://progress.capitalmind.in/", "//input[@name='email']")
#print("Login form has loaded")

# Enter userid and password
userid_element = browser.find_elements("xpath", "//input[@name='email']")
if len(userid_element) != 1:
	print('No unique userid input box: %d' % len(userid_element))
	exception_quit(browser)
userid_element[0].send_keys(userid)

passwd_element = browser.find_elements("xpath", "//input[@name='password']")
if len(passwd_element) != 1:
	print('No unique passwd input box: %d' % len(passwd_element))
	exception_quit(browser)
passwd_element[0].send_keys(passwd)

#print("Entered userid and password")

login_element = browser.find_elements("xpath", "//button[@type='submit']")
if len(login_element) != 1:
	print('No unique login button: %d' % len(login_element))
	exception_quit(browser)
login_element[0].click()

#print("Clicked the login button")

# Wait for dashboard to load
val_element_path = "//h6[@class='jss94 jss111 jss185']"
wait_load(browser, timeout, val_element_path)
print("Dashboard has loaded")

# parse the holdings table
val_element = browser.find_elements("xpath", val_element_path)
if len(val_element) < 1:
	print('Not enough value elements: %d < 1' % len(val_element))
	exception_quit(browser)
#for i in range(len(val_element)): print(val_element[i].get_attribute('title'))

def get_num(s):
	return float(re.findall(r"\d+\.?\d+", s.replace(',',''))[0])

#totValue = get_num(val_element[0].text)
curValue = get_num(val_element[0].get_attribute('title'))

browser.quit()

#print(totValue, curValue)
df = pd.DataFrame([[0, curValue]], columns = ['Total', 'Current'])
print(df)

fname = basecm + todaystr +'.xlsx'
df.to_excel(fname, index=False)
print("\nWritten %d rows to file %s ..." % (len(df), fname))
print('-------------------------------------------------------')




