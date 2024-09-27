from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import pandas as pd 
import time
import sys

import configparser
import argparse
import re

def get_num(x):
    return float(''.join(ele for ele in x if ele.isdigit() or ele == '.'))

timeout = 30

def exception_quit(browser):
    browser.quit()
    sys.exit(1)

def wait_load(browser, timeout, xpath):
    print("%s: Waiting (timeout %d s) for [%s]" % (time.strftime('%H:%M:%S', time.gmtime(time.time())), timeout, xpath))
    try:
        WebDriverWait(browser, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
    except TimeoutException:
        print("Timed out waiting for page to load")
        #print(browser.page_source)
        exception_quit(browser)

def load_page(browser, url, xpath):
    browser.get(url)
    print("%s: Loading %s ..." % (time.strftime('%H:%M:%S', time.gmtime(time.time())), url))
    wait_load(browser, timeout, xpath)

def idle_wait_for(t):
    if args.verbose: print('Waiting %d seconds ...' % t)
    for i in range(t):
        time.sleep(1)

def get_idfcbank_details(userid, username, password, cname, verbose):#, num_accounts):
    # Create new Instance of Chrome in incognito mode
    # Specifying incognito mode as you launch your browser[OPTIONAL]
    option = webdriver.ChromeOptions()
    #option.add_argument("--incognito")
    prefs = {"profile.default_content_setting_values.geolocation" :1}
    option.add_experimental_option("prefs",prefs)
    #option.add_argument("disable-geolocation")
    #option.add_argument("--headless")
    browser = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver', options=option)

    # Go to desired website
    load_page(browser, "https://app.mfcentral.com/investor/signin", "//button[@data-testid='submit-button-id']")
    if verbose: print("Login form has loaded, waiting for stability ...")
    idle_wait_for(5)

    userid_element = browser.find_elements_by_xpath("//input[@data-testid='phone-number-id']")
    if len(userid_element) != 1:
        print('No unique userid input box: %d' % len(userid_element))
        exception_quit(browser)
    userid_element[0].send_keys(userid)

    continue_element = browser.find_elements_by_xpath("//button[@data-testid='submit-button-id']")
    if len(continue_element) < 1:
        print('No continue button: %d' % len(continue_element))
        exception_quit(browser)
    continue_element[0].click()

    if verbose: print("Entered userid and clicked the continue button ...")
    idle_wait_for(10)

    uname_element = browser.find_elements_by_xpath("//input[@data-testid='user-name-id']")
    if len(uname_element) > 0: 
        if verbose: print("Found user-name-id input field ...")
        uname_element[0].send_keys(username)
        proceed_element = browser.find_elements_by_xpath("//button[@data-testid='proceed-button']")
        if len(proceed_element) < 1:
            print('No proceed button: %d' % len(proceed_element))
            exception_quit(browser)
        proceed_element[0].click()
        if verbose: print('Entered username and clicked proceed button ...')
    else:
        if verbose: print("NOT Found user-name-id input field ...")


    wait_load(browser, timeout, "//input[@data-testid='password-input']")
    
    passwd_element = browser.find_elements_by_xpath("//input[@data-testid='password-input']")
    if len(passwd_element) != 1:
        print('No unique passwd input box: %d' % len(passwd_element))
        exception_quit(browser)
    passwd_element[0].send_keys(passwd)

    login_element = browser.find_elements_by_xpath("//button[@data-testid='login-button']")
    if len(login_element) != 1:
        print('No unique login button: %d' % len(login_element))
        exception_quit(browser)
    login_element[0].click()

    if verbose: print("Entered password and clicked the login button")

    #wait_load(browser, timeout, "//p[@data-testid='AccountNumber']")
    wait_load(browser, timeout, "//p[@data-testid='account-number']")
    if verbose: print("Dashboard has loaded, waiting for stability ...")
    idle_wait_for(5)

    # parse account number
    account_element = browser.find_elements_by_xpath("//p[@data-testid='account-number']")
    if len(account_element) != 1:
        print('No unique account element: %d' % len(account_element))
        exception_quit(browser)
    el = account_element[0]
    acno = get_num(el.text)
    if verbose: print('Account number: %d' % acno)

    visible_element = browser.find_elements_by_xpath("//div[@data-testid='arrow-indicator']")
    if len(visible_element) != 1:
        print('No unique arrow button: %d' % len(visible_element))
        exception_quit(browser)
    visible_element[0].click()

    if verbose: print("Clicked the arrow button")
    wait_load(browser, timeout, "//div[@data-testid='AccountBalance']")
    idle_wait_for(5)

    # parse amount
    amount_element = browser.find_elements_by_xpath("//div[@data-testid='AccountBalance']")
    if len(amount_element) != 1:
        print('No unique amount element: %d' % len(amount_element))
        exception_quit(browser)
    print(amount_element[0].text)
    amount = get_num(amount_element[0].text)
    if verbose: print('Amount: %d' % amount)

    browser.quit()
    return [acno, cname, amount]

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

bank_configs = [x for x in config.sections() if x.startswith('bank-idfc-')]

data = config['data']
basebankidfc = data['basebankidfc']

all_accounts = []
for i in range(len(bank_configs)):
    bank_config_name = bank_configs[i]
    bank = bank_config_name.split('-')[1]
    cname = bank_config_name.split('-')[2]
    bank_config = config[bank_config_name]
    userid = bank_config['userid'] 
    username = bank_config['username'] 
    passwd = bank_config['passwd'] 
    print("****", bank_config_name, ":", userid, username, cname, "****\n")
    if (i > 0): idle_wait_for(30)
    account = get_idfcbank_details(userid, username, passwd, cname, args.verbose)
    all_accounts.append(account)

df = pd.DataFrame(all_accounts, columns=['Account', 'Name', 'Amount'])
print(df)

fname = basebankidfc + todaystr + '.xlsx'
df.to_excel(fname, index=False)

print("\nWritten %d rows to file %s ..." % (len(df), fname))
print('-------------------------------------------------------')





