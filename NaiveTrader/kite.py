#!/usr/bin/env python
# coding: utf-8
"""
- Get NSE Holiday Indicators
- Generate Request Token for Zerodha Kite  
- Get Kite Orders & positions  
"""

# Import Modules
import pandas as pd, numpy as np
from kiteconnect import KiteConnect
from selenium import webdriver
import pyotp, time
import datetime as dt


def get_nse_holiday_ind(holiday_list_fname):
    """
    Parameters
    ----------
        holiday_list_fname: str, NSE Holiday list file name, available @ https://www.nseindia.com/resources/exchange-communication-holidays#href-1
    Returns
    -------
        boolean string whether today is a holiday
    """
    # Import NSE Holiday List
    holiday_list_df = pd.read_csv(holiday_list_fname)
    holiday_list_df['DATE'] = pd.to_datetime(holiday_list_df['DATE'], format='%d-%b-%Y')
    curr_year_holiday_list = holiday_list_df['DATE'].tolist()

    # Do not generate access token on a holiday/ weekend
    return(pd.Timestamp(dt.datetime.now().date()) in holiday_list_df['DATE'].tolist())


def get_nse_holiday_list(chromedriver):
    """
    Parameters
    ----------
        chromedriver: chromedriver file with location. check the chrome version before using the chromedriver
    Returns
    -------
        NSE holiday list
    """
    # Start the Webdriver and Open the NSE holiday list url
    driver = webdriver.Chrome(chromedriver)
    driver.get('https://www.nseindia.com/resources/exchange-communication-holidays#href-0')
    driver.implicitly_wait(10)

    # Extract Holiday List Table
    while True:
        try:
            holiday_table = driver.find_element_by_xpath('//*[@id="holidayTable"]/tbody')
            holiday_list = [pd.to_datetime(row.find_elements(By.TAG_NAME, "td")[1].text, format='%d-%b-%Y') for row in holiday_table.find_elements(By.TAG_NAME, "tr")]
            if len(holiday_list) > 0:
                break
        except:
            pass
    # Close Web Driver
    driver.quit()

    return(holiday_list)


def kite_auth_connect(chromedriver, token_fname):
    """
    Parameters
    ----------
        chromedriver: str, chromedriver file with location. check the chrome version before using the chromedriver
        token_fname: str, kite login information file with location. Please refer to existing files for required format
    Returns
    -------
        request token, which will be required to establish connection to execute trades
    """
    key_secret = open(token_fname,'r').read().split()
    kite = KiteConnect(api_key=key_secret[0])
    service = webdriver.chrome.service.Service(chromedriver)
    service.start()
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options = options.to_capabilities()
    driver = webdriver.Remote(service.service_url, options)
    driver.get(kite.login_url())
    driver.implicitly_wait(10)
    username = driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[1]/input')
    password = driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[2]/input')
    username.send_keys(key_secret[2])
    password.send_keys(key_secret[3])
    driver.find_element_by_xpath('/html/body/div[1]/div/div/div[1]/div/div/div/form/div[4]/button').click()
    pin = driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[2]/div/input')
    totp = pyotp.TOTP(key_secret[4])
    pin.send_keys(totp.now())
    driver.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[1]/div/div/div[2]/form/div[3]/button').click()
    time.sleep(10)
    request_token=driver.current_url.split('&request_token')[1].split('=')[1]
    driver.quit()
    return(request_token)

def connect_kite(auth_loc):
    """
    Parameters
    ----------
        auth_loc: str, location where kite api key and access token files are stored
    Returns
    -------
        kite: kite object
    """
    access_token = open(f"{auth_loc}/access_token.txt",'r').read()
    key_secret = open(f"{auth_loc}/api_key.txt",'r').read().split()
    kite = KiteConnect(api_key=key_secret[0])
    kite.set_access_token(access_token)
    return(kite)


def get_positions(kite):
    """
    Parameters
    ----------
        kite: kite object
    Returns
    -------
        pandas dataframe of kite positions
    """
    pos_df = pd.DataFrame(kite.positions()['day'])
    pos_df = pos_df[['tradingsymbol', 'exchange', 'instrument_token', 'product', 'quantity', 'average_price', 'value', 'pnl',
                     'buy_quantity', 'buy_price', 'buy_value', 'sell_quantity', 'sell_price', 'sell_value']]

    pos_df['last_price'] = pos_df['instrument_token'].apply(lambda x: kite.quote(x)[f'{x}']['last_price'])
    return(pos_df)


def get_orders(kite):
    """
    Parameters
    ----------
        kite: kite object
    Returns
    -------
        pandas dataframe of kite orders
    """
    order_df = pd.DataFrame(kite.orders())
    order_df = order_df[['order_id', 'status', 'order_timestamp', 'variety', 'exchange', 'tradingsymbol', 'instrument_token', 'order_type',
                         'transaction_type', 'product', 'quantity', 'price', 'trigger_price', 'average_price']]
    return(order_df)
