from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains

import pandas as pd 
import time
import sys
import re

import argparse
import configparser

now = time.time()
nowstr = time.strftime('%Y-%m-%d_%H-%M-UTC', time.gmtime(now))
todaystr = time.strftime('%Y-%m-%d', time.gmtime(now))

timeout = 20

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

def get_cams_report(user, verbose):
    print('\nRequesting CAMS report for %s:%s ...\n' % (user['email'], user['pan']))

    # Specifying incognito mode as you launch your browser[OPTIONAL]
    option = webdriver.ChromeOptions()
    #option.add_argument("--incognito")
    #option.add_argument("--headless")
    option.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    # Create new Instance of Chrome in incognito mode
    service = Service(executable_path='/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=option)

    # Go to desired website
    t = load_page(driver, "https://www.camsonline.com/Investors/Statements/Consolidated-Account-Statement", "//button[@type='submit']")
    print("CAMS page has loaded in ", t)

    wait_load(driver, timeout, "//input[@value='PROCEED']")
    if verbose: print('Disclaimer page loaded')

    #driver.switch_to.active_element
    #driver.find_element(By.CSS_SELECTOR, "div[class='cdk-overlay-backdrop cdk-overlay-dark-backdrop cdk-overlay-backdrop-showing']").click()
    #print('Clicked overlay')
    #driver.find_element(By.CSS_SELECTOR, "span[class='mat-radio-container']").click() 
    #element = driver.find_element(By.CSS_SELECTOR, "span[class='mat-radio-label-content']")

    time.sleep(5)
    #input("Enter something to continue ...")

    element = driver.find_element(By.CSS_SELECTOR, "input[type='radio'][value='ACCEPT']")

    action = ActionChains(driver)
    action.move_to_element(element).click().perform()

    if verbose: print('Clicked ACCEPT')

    driver.find_element(By.CSS_SELECTOR, "input[type='button'][value='PROCEED']").click() 
    if verbose: print('Clicked PROCEED')

    time.sleep(2)
    #e = driver.find_element(By.XPATH, "//*[@id='mat-dialog-1']/app-camsterms/div/div/mat-icon")
    #if e: e.click()

    #input("Enter something to continue ...")
    #//*[@id="mat-dialog-1"]/app-camsterms/div/div/mat-icon
    wait_load(driver, timeout, "//div[@class='close-icon colsebanner']")

    elements = driver.find_elements(By.CSS_SELECTOR, "mat-icon[class*='close-popup']")
    #for e in elements: print('mat_icon:', e, e.text)
    action.move_to_element(elements[0]).click().perform()
    if verbose: print('Clicked close icon')

    driver.find_element(By.CSS_SELECTOR, "mat-radio-button[value='detailed']").click() 
    time.sleep(1)
    driver.find_element(By.CSS_SELECTOR, "mat-radio-button[value='SP']").click() 
    time.sleep(1)
    driver.find_element(By.CSS_SELECTOR, "mat-radio-button[value='YT']").click() 
    time.sleep(1)

    # enter from_date
    driver.find_element(By.CSS_SELECTOR, "mat-datepicker-toggle").click()
    if verbose: print("Clicked datepicker")
    time.sleep(1)
    driver.find_element(By.XPATH, "//*[@id='mat-datepicker-1']/mat-calendar-header/div/div/button[1]").click()
    if verbose: print("Clicked multi-year selector")
    time.sleep(1)
    driver.find_element(By.XPATH, "//*[@id='mat-datepicker-1']/div/mat-multi-year-view/table/tbody/tr[1]/td[1]/div[1]").click()
    if verbose: print("Selected year")
    time.sleep(1)
    driver.find_element(By.XPATH, "//*[@id='mat-datepicker-1']/div/mat-year-view/table/tbody/tr[2]/td[1]/div[1]").click()
    if verbose: print("Selected month")
    time.sleep(1)

    #input()
#/html/body/div[3]/div[2]/div/mat-datepicker-content/div[2]/mat-calendar/div/mat-month-view/table/tbody/tr[2]/td[2]/div[1]
    driver.find_element(By.XPATH, "//*[@id='mat-datepicker-1']/div/mat-month-view/table/tbody/tr[2]/td[2]/div[1]").click()
    if verbose: print("Selected day")
    time.sleep(1)

    #element = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='from_date']") 
    #driver.execute_script("arguments[0].value='01-Jan-2000'", element)
    #driver.execute_script("arguments[0].value='2000-01-01'", element)
    #print(element, element.text)

    # enter email id
    driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='email_id']").send_keys(user['email']) 
    time.sleep(1)

    # enter PAN
    element = driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='pan']")
    delay_between_keys = 0.3
    for c in user['pan']:
        action.send_keys_to_element(element, c).perform()
        time.sleep(delay_between_keys)
    if verbose: print("Entered PAN")

    # enter password
    driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='password']").send_keys(user['pan']) 
    time.sleep(1)
    driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='confirmPassword']").send_keys(user['pan']) 
    time.sleep(1)

    #input("All inputs done, Enter something to submit ...")

    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click() 
    if verbose: print("Clicked submit")
    time.sleep(5)
    #input("Enter something to continue ...")

    driver.quit()

# ---------------------------------------------------------------------

P = argparse.ArgumentParser(description="__doc__")
P.add_argument("-c", "--config", type=str, default='config.ini', help="Config file")
P.add_argument("-u", "--user", type=str, default=None, help="User")
P.add_argument("-v", "--verbose", action='store_true', help="Verbose mode")
args = P.parse_args()

config = configparser.ConfigParser()
config.read(args.config)
#print(config.sections())

cam_configs = [x for x in config.sections() if x.startswith('cam-')]
if args.user is not None:
    print('User: %s' % args.user)
    cam_configs = [x for x in cam_configs if x.endswith(args.user)]
    print(cam_configs)
    
for c in cam_configs:
    user = {'email': config[c]['email'], 'pan':config[c]['pan']}
    #print(c, user)
    get_cams_report(user, args.verbose)




