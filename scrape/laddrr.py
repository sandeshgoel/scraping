from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import pandas as pd 
import time
import sys
import re

now = time.time()
nowstr = time.strftime('%Y-%m-%d_%H-%M-UTC', time.gmtime(now))
todaystr = time.strftime('%Y-%m-%d', time.gmtime(now))

timeout = 6

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
	t1 = time.time()
	browser.get(url)
	print("%s: Loading %s ..." % (time.strftime('%H:%M:%S', time.gmtime(time.time())), url))
	wait_load(browser, timeout, xpath)
	t2 = time.time()
	return (t2-t1)

# Specifying incognito mode as you launch your browser[OPTIONAL]
option = webdriver.ChromeOptions()
option.add_argument("--incognito")
#option.add_argument("--headless")

# Create new Instance of Chrome in incognito mode
browser = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver', options=option)

# Go to desired website
t = load_page(browser, "https://laddrr.com/", "//div[@data-elementor-type='header']")
print("Laddrr page has loaded in ", t)

t = load_page(browser, "https://laddrr.com/blog/", "//article")
print("Laddrr blog page has loaded in ", t)

t = load_page(browser, "https://laddrr.com/laddrrup/", "//form[@id='la-filter']")
print("Laddrrup page has loaded in ", t)

# Enter userid and password
form_element = browser.find_elements_by_xpath("//form[@id='la-filter']")
if len(form_element) != 1:
	print('No unique form: %d' % len(userid_element))
	exception_quit(browser)
print(form_element[0].text)

browser.quit()





