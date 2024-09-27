from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import pandas as pd 
import time
import sys

import configparser

config = configparser.ConfigParser()
config.read('config.ini')
#print(config.sections())

zerodha = config['zerodha']
userid = zerodha['userid'] 
passwd = zerodha['passwd'] 
pin = zerodha['pin'] 

data = config['data']
basezerodha = data['basezerodha']

print(userid, pin, basezerodha)

now = time.time()
nowstr = time.strftime('%Y-%m-%d_%H-%M-UTC', time.gmtime(now))
todaystr = time.strftime('%Y-%m-%d', time.gmtime(now))

timeout = 60

def exception_quit(browser):
	browser.quit()
	sys.exit(1)

def wait_load(browser, timeout, xpath):
	print("%s: Waiting for %d seconds [%s]" % (time.strftime('%H:%M:%S', time.gmtime(time.time())), timeout, xpath))
	try:
		WebDriverWait(browser, timeout).until(EC.visibility_of_element_located((By.XPATH, xpath)))
	except TimeoutException:
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

# Create new Instance of Chrome in incognito mode
browser = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver', options=option)

# Go to desired website
load_page(browser, "https://kite.zerodha.com/", "//div[@class='form-header text-center']")
print("Login form has loaded")

# Enter userid and password
userid_element = browser.find_elements_by_xpath("//input[@id='userid']")
if len(userid_element) != 1:
	print('No unique userid input box: %d' % len(userid_element))
	exception_quit(browser)
userid_element[0].send_keys(userid)

passwd_element = browser.find_elements_by_xpath("//input[@id='password']")
if len(passwd_element) != 1:
	print('No unique passwd input box: %d' % len(passwd_element))
	exception_quit(browser)
passwd_element[0].send_keys(passwd)

print("Entered userid and password")

login_element = browser.find_elements_by_xpath("//button[@type='submit']")
if len(login_element) != 1:
	print('No unique login button: %d' % len(login_element))
	exception_quit(browser)
login_element[0].click()

print("Clicked the login button")

# Wait for PIN form to load
wait_load(browser, timeout, "//input[@label='PIN']")
print("PIN form has loaded")

# Enter PIN
pin_element = browser.find_elements_by_xpath("//input[@label='PIN']")
if len(pin_element) != 1:
	print('No unique pin input box: %d' % len(pin_element))
	exception_quit(browser)
pin_element[0].send_keys(pin)

print("Entered PIN")

login_element = browser.find_elements_by_xpath("//button[@type='submit']")
if len(login_element) != 1:
	print('No unique continue button: %d' % len(login_element))
	exception_quit(browser)
login_element[0].click()

print("Clicked the continue button")

# Wait for dashboard to load
wait_load(browser, timeout, "//div[@class='six columns market-overview-block']")
print("Dashboard has loaded")

# Go to desired website
load_page(browser, "https://console.zerodha.com/portfolio/holdings/", "//*")
# for some reason, first time it redirects to dashboard, so load again
load_page(browser, "https://console.zerodha.com/portfolio/holdings/", "//table[@id='holdings_table']")
print("Holdings has loaded")

# parse the holdings table
table_element = browser.find_elements_by_xpath("//table[@id='holdings_table']")
if len(table_element) != 1:
	print('No unique table: %d' % len(table_element))
	exception_quit(browser)
headers_element = table_element[0].find_elements_by_xpath(".//thead/tr/th")
col_headers = [x.text for x in headers_element]

value_rows = []
rows_element = table_element[0].find_elements_by_xpath(".//tbody/tr")
for row in rows_element:
	values_element = row.find_elements_by_xpath("./td")
	col_values = [x.text for x in values_element]
	value_rows.append(col_values)

browser.quit()

print("Table has been parsed")

df = pd.DataFrame(value_rows, columns=col_headers)
#print(df)

fname = basezerodha + todaystr +'.xlsx'
df.to_excel(fname, index=False)
print("\nWritten %d rows to file %s ..." % (len(df), fname))
print('-------------------------------------------------------')




