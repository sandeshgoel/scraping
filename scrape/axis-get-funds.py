from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service

import pandas as pd 
import time
import sys

import configparser
import argparse
import re

timeout = 60

def exception_quit(browser):
	input('press key ...')
	browser.quit()
	sys.exit(1)

def wait_load(browser, timeout, xpath):
	print("%s: Waiting for %d seconds [%s]" % (time.strftime('%H:%M:%S', time.gmtime(time.time())), timeout, xpath))
	try:
		WebDriverWait(browser, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
	except TimeoutException:
		print("Timed out waiting for page to load")
		exception_quit(browser)

def load_page(browser, url, xpath):
	browser.get(url)
	print("%s: Loading %s ..." % (time.strftime('%H:%M:%S', time.gmtime(time.time())), url))
	wait_load(browser, timeout, xpath)

def print_all_elements(browser):
	print('Printing all elements')
	all_ele = browser.find_elements("xpath", "//*")
	for e in all_ele:
		print(e.tag_name, e.get_attribute("id"), e.get_attribute("name"), e.get_attribute("class"))
	#input('Press a key ...')

def get_axisbank_details(userid, password, verbose):#, num_accounts):
	# Specifying incognito mode as you launch your browser[OPTIONAL]
	option = webdriver.ChromeOptions()
	option.add_argument("--incognito")
	#option.add_argument("--headless")
	option.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
	# Create new Instance of Chrome in incognito mode
	service = Service(executable_path='/usr/local/bin/chromedriver')
	#service = Service(executable_path='/opt/homebrew/bin/chromedriver')
	browser = webdriver.Chrome(service=service, options=option)

	# Go to desired website
	load_page(browser, "https://omni.axisbank.co.in/axisretailbanking/", "//input[@id='custid']")
	if verbose: print("Login form has loaded")

	#browser.switch_to.frame('login_page')

	userid_element = browser.find_elements(By.XPATH, "//input[@id='custid']")
	if len(userid_element) != 1:
		print('No unique userid input box: %d' % len(userid_element))
		exception_quit(browser)
	userid_element[0].send_keys(userid)

	passwd_element = browser.find_elements("xpath",  '//input[@id="pass"]')#'//*[@id="keyboard"]')
	if len(passwd_element) != 1:
		print('No unique passwd input box: %d' % len(passwd_element))
		exception_quit(browser)
	passwd_element[0].send_keys(passwd)

	login_element = browser.find_elements("xpath", "//button[@id='APLOGIN']")
	if len(login_element) != 1:
		print('No unique login button: %d' % len(login_element))
		exception_quit(browser)
	login_element[0].click()

	if verbose: print("Entered password and checkbox and clicked the login button")

	#path = "//div[@class='cardHeader ng-star-inserted']"
	path = "//div[@class='cards rCard0']"
	wait_load(browser, timeout, path)
	time.sleep(10)

	ac_element = browser.find_elements("xpath", path)
	if len(ac_element) == 0:
		print('No account element: %d' % len(ac_element))
		exception_quit(browser)

	#for e in ac_element: print(e.text)
	if verbose: print(ac_element[0].text)
	amount_str =  ac_element[0].text.replace(',','').split('\n')[3]
	if verbose: print(f'Amount: {amount_str}')
	
	accounts = []
	account = (userid, userid, re.findall(r'\d+', amount_str)[0])
	print(account)
	accounts.append(account)

	browser.quit()
	return accounts

# -------------------------------------------------------------------------------------------

now = time.time()
nowstr = time.strftime('%Y-%m-%d_%H-%M-UTC', time.gmtime(now))
todaystr = time.strftime('%Y-%m-%d', time.gmtime(now))

P = argparse.ArgumentParser(description="__doc__")
P.add_argument("-c", "--config", type=str, default='config.ini', help="Config file")
P.add_argument("-v", "--verbose", action='store_true', help="Verbose mode")
args = P.parse_args()

config = configparser.ConfigParser()
config.read(args.config)
#print(config.sections())

bank_configs = [x for x in config.sections() if x.startswith('bank-axis-')]

data = config['data']
basebankaxis = data['basebankaxis']

all_accounts = []
for bank_config_name in bank_configs:
	bank = bank_config_name.split('-')[1]
	cname = bank_config_name.split('-')[2]
	bank_config = config[bank_config_name]
	userid = bank_config['userid'] 
	passwd = bank_config['passwd'] 
	print("\n****", bank_config_name, ":", userid, cname, "****")
	accounts = get_axisbank_details(userid, passwd, args.verbose)
	for account in accounts:
		if account[0] not in ['TOTAL']+[x[0] for x in all_accounts]:
			all_accounts.append(account)

df = pd.DataFrame(all_accounts, columns=['Account', 'Name', 'Amount'])
print("")
print(df)

fname = basebankaxis + todaystr + '.xlsx'
df.to_excel(fname, index=False)

print("Written %d rows to file %s ..." % (len(df), fname))
print('-------------------------------------------------------')





