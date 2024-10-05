from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import configparser
import time
import pandas as pd
import sys

def get_gold_rate():
    try:
        option = webdriver.ChromeOptions()
        option.add_argument("--incognito")
        #option.add_argument("--headless")
        option.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        # Create new Instance of Chrome in incognito mode
        service = Service(executable_path='/usr/local/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=option)

        # Open the website
        driver.get("https://www.ibjarates.com/")
        

        xpath = '//*[@id="lblrate24K"]'
        #full_xpath = '/html/body/form/div[5]/div[1]/div[1]/div[1]/div[1]/div[1]/div/div/ul/li/div/div[1]/h3/span[1]'
        # Find the gold rate element
        #gold_rate_element = driver.find_element(By.CLASS_NAME, "gold-rate-value")
        gold_rate_element = driver.find_element(By.XPATH, xpath)

        # Extract the gold rate
        gold_rate = gold_rate_element.text.strip()
        
        # Close the browser session
        driver.quit()
        
        return gold_rate
    except Exception as e:
        print("An error occurred: {}".format(str(e)))
        return -1

if __name__ == "__main__":        
    config = configparser.ConfigParser()
    config.read('config.ini')
    data = config['data']
    basegold = data['basegold']
    print(basegold)

    gold_rate = get_gold_rate()
    gold_rate = int(float(gold_rate))
    print("Latest gold rate:", gold_rate)

    if gold_rate == -1:
        sys.exit(1)
        
    now = time.time()
    nowstr = time.strftime('%Y-%m-%d_%H-%M-UTC', time.gmtime(now))
    todaystr = time.strftime('%Y-%m-%d', time.gmtime(now))

    df = pd.DataFrame([[gold_rate]], columns = ['Gold Rate'])
    print(df)

    fname = basegold + todaystr +'.xlsx'
    df.to_excel(fname, index=False)

    print("\nWritten %d rows to file %s ..." % (len(df), fname))
    print('-------------------------------------------------------')
    
    
