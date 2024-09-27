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

timeout = 30

def exception_quit(browser):
	#input('press key ...')
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

def get_hdfcbank_details(userid, password, verbose):#, num_accounts):
	# Specifying incognito mode as you launch your browser[OPTIONAL]
	option = webdriver.ChromeOptions()
	option.add_argument("--incognito")
	#option.add_argument("--headless")
	option.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
	# Create new Instance of Chrome in incognito mode
	service = Service(executable_path='/usr/local/bin/chromedriver')
	browser = webdriver.Chrome(service=service, options=option)

	# Go to desired website
	load_page(browser, "https://netbanking.hdfcbank.com/netbanking/", "//frame[@name='login_page']")
	#print("Login form has loaded")

	browser.switch_to.frame('login_page')

	userid_element = browser.find_elements(By.XPATH, "//input[@name='fldLoginUserId']")
	if len(userid_element) != 1:
		print('No unique userid input box: %d' % len(userid_element))
		exception_quit(browser)
	userid_element[0].send_keys(userid)

	#login_element = browser.find_elements("xpath", "//img[@alt='continue']")  - changed 16/8/21
	#login_element = browser.find_elements("xpath", "//div[@class='inputfield ibvt loginData']")
	login_element = browser.find_elements(By.XPATH, "//a[@class='btn btn-primary login-btn']")
	if len(login_element) < 1:
		print('No continue button: %d' % len(login_element))
		exception_quit(browser)
	login_element[0].click()

	if verbose: print("Entered userid and clicked the continue button")

	time.sleep(10) # wait for password field to load
	browser.switch_to.default_content()
	#passwd_element = browser.find_elements("xpath", "//input[@name='fldPassword']")
	#xpath = '/html/body/div[1]/div/div[2]/div[2]/div[2]/div[3]/div/div/div[2]/div/div/div[1]/div/div[2]/div[3]/div/div[2]/div[1]/div[3]/div[1]/div[2]/div[1]/hdfc-specialchar/div/md-input-container/input'
	#//*[@id="keyboard"]	
	passwd_element = browser.find_elements("xpath",  '//*[@id="keyboard"]')#'//*[@id="keyboard"]')
	if len(passwd_element) != 1:
		print('No unique passwd input box: %d' % len(passwd_element))
		exception_quit(browser)
	passwd_element[0].send_keys(password)

	#//*[@id="secureAccessID"]
	#/html/body/div[1]/div/div[2]/div[2]/div[2]/div[3]/div/div/div[2]/div/div/div[1]/div/div[2]/div[3]/div/div[2]/div[1]/div[3]/div[1]/div[2]/div[3]/div[2]/hdfc-checkbox/div/input
	chk_element = browser.find_elements("xpath", '//*[@id="secureAccessID"]')
	if len(chk_element) != 1:
		print('No unique check box: %d' % len(chk_element))
		exception_quit(browser)
	chk_element[0].click()

	#login_element = browser.find_elements("xpath", "//img[@alt='Login']") - changed 16/8/21
	#login_element = browser.find_elements("xpath", "//a[@class='btn btn-primary login-btn']")
	login_element = browser.find_elements("xpath", "//*[@id='loginBtn']")
	if len(login_element) != 1:
		print('No unique login button: %d' % len(login_element))
		exception_quit(browser)
	login_element[0].click()

	if verbose: print("Entered password and checkbox and clicked the login button")

	#wait_load(browser, timeout, "//*[@id='SavingTotalSummary']")
	#wait_load(browser, timeout, "//frame[@name='main_part']")
	#//*[@id="common_menu1"]
	#//*[@id="left_menu"]
	#wait_load(browser, timeout, "//frame[@name='left_menu']") -- for some reason this is failing 31/10/23
	time.sleep(10)

	ul_element = browser.find_elements("xpath", '//*[@id="savingsTabPane"]/section/div/div/div[1]/ul')
	if len(ul_element) != 1:
		print('No unique ul element: %d' % len(ul_element))
		exception_quit(browser)

	#all_li = ul_element[0].find_elements(By.TAG_NAME, "li")
	all_li = ul_element[0].find_elements(By.XPATH, "./li")
	print('Number of accounts:', len(all_li))

	#for li in all_li: print(li.text)

	accounts = []
	for i in range(len(all_li)):
		xpath = '//*[@id="savingsTabPane"]/section/div/div/div[1]/ul/li[%d]/ul/li[1]/p[2]' % (i+1)
		ac_element = browser.find_elements("xpath", xpath)
		if len(ac_element) != 1:
			print('No unique account element: %d' % len(ac_element))
			exception_quit(browser)
		xpath =	'//*[@id="savingsTabPane"]/section/div/div/div[1]/ul/li[%d]/ul/li[2]/p/decimal-casing/span[2]' % (i+1)
		val_element = browser.find_elements("xpath", xpath)
		if len(val_element) != 1:
			print('No unique value element: %d' % len(val_element))
			exception_quit(browser)
		account = (ac_element[0].text, userid, float(val_element[0].text.replace(',','')))
		print(i, account)
		accounts.append(account)

	browser.quit()
	return accounts

	# -------- obsolete code

	if args.verbose:
		elements = browser.find_elements("xpath", "//frame")
		for e in elements: print(e.tag_name, e.get_attribute('id'), e.get_attribute('outerHTML'))
		if len(elements) == 0:
			print('No frame element found')
			print(browser.page_source)
			input('Enter to continue')
			#exception_quit(browser)

	#load_page(browser, "https://netbanking.hdfcbank.com/netbanking/entry", "//*")
	print("%s: Dashboard has loaded" % (time.strftime('%H:%M:%S', time.gmtime(time.time()))))

	try:
		browser.switch_to.default_content()
	except Exception as e:
		print("Can't switch, exception", e)
		exception_quit(browser)

	try:
		browser.switch_to.frame('left_menu')
	except Exception as e:
		print("Can't find left_menu, exception", e)
		exception_quit(browser)

	# parse the menu
	menu_element = browser.find_elements("xpath", "//ul[@class='accordion']")
	if len(menu_element) < 1:
		print('No unique menu option: %d' % len(menu_element))
		exception_quit(browser)
	#print(menu_element[0].get_attribute("outerHTML"))

	button_element = menu_element[0].find_elements("xpath", "//*[text()='Account Summary']")
	if len(button_element) < 1:
		print('No unique account button: %d' % len(button_element))
		exception_quit(browser)
	#print(button_element[0].get_attribute("outerHTML"))
	click_element = button_element[0].find_elements("xpath", "..")
	#print(click_element[0].get_attribute("outerHTML"))
	click_element[0].click()
	if verbose: print("Clicked the Account Summary menu\n")

	try:
		browser.switch_to.default_content()
	except Exception as e:
		print("Can't switch2, exception", e)
		exception_quit(browser)

	browser.switch_to.frame('main_part')

	# parse the holdings table
	table_element = browser.find_elements("xpath", "//table[@class='datatable landTable']")
	if len(table_element) < 1:
		print('No table: %d' % len(table_element))
		exception_quit(browser)

	rows_element = table_element[0].find_elements("xpath", ".//tbody/tr")
	#print("%d rows found, num_accounts %d" % (len(rows_element), num_accounts))
	accounts = []
	for i, row in enumerate(rows_element):
		parsing_failed = False
		td_elements = row.find_elements("xpath", "./td")
		if verbose: print("Row %d: number of cells %d" % (i, len(td_elements)))
		if i == 0: # first row is summary, contains only one td
			amt_element = td_elements[0].find_elements("xpath", "./span[@id='SavingTotalSummary']")
			amt = amt_element[0].text
			amt = re.findall(r"\d+\.?\d+", amt.replace(',',''))[0]
			account = ['TOTAL', '', float(amt)]
		else: # other rows contain account details in 4 td's
			try:
				ac_element = td_elements[0].find_elements("xpath", "./a")
				ac = ac_element[0].get_attribute("text")

				name_element = td_elements[2].find_elements("xpath", "./span")
				name = name_element[1].get_attribute("innerHTML")

				amt_element = td_elements[3].find_elements("xpath", "./span")
				amt = amt_element[1].get_attribute("innerHTML")
				amt = re.findall(r"\d+\.?\d+", amt)

				account = [ac.strip(), name, float(amt[0])]
			except:
				if verbose: print("\tParsing failed")
				parsing_failed = True
		if parsing_failed: continue
		if verbose: print('\t', account)
		accounts.append(account)
		#if num_accounts > 0 and i >= num_accounts: break

	tot = 0
	for ac in accounts[1:]:
		tot += ac[2] if not ac[0].startswith('5500000') else 0
	if abs(tot - accounts[0][2]) > 0.1:
		print("\n**** TOTAL inconsistent: %f %f ****\n" % (tot, accounts[0][2]))
	else:
		if verbose: print("TOTAL is consistent\n")
	
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

bank_configs = [x for x in config.sections() if x.startswith('bank-hdfc-')]

data = config['data']
basebankhdfc = data['basebankhdfc']

all_accounts = []
for bank_config_name in bank_configs:
	bank = bank_config_name.split('-')[1]
	cname = bank_config_name.split('-')[2]
	bank_config = config[bank_config_name]
	userid = bank_config['userid'] 
	passwd = bank_config['passwd'] 
	print("\n****", bank_config_name, ":", userid, cname, "****")
	accounts = get_hdfcbank_details(userid, passwd, args.verbose)#, num_accounts)
	for account in accounts:
		if account[0] not in ['TOTAL']+[x[0] for x in all_accounts]:
			all_accounts.append(account)

df = pd.DataFrame(all_accounts, columns=['Account', 'Name', 'Amount'])
print("")
print(df)

fname = basebankhdfc + todaystr + '.xlsx'
df.to_excel(fname, index=False)

print("Written %d rows to file %s ..." % (len(df), fname))
print('-------------------------------------------------------')





