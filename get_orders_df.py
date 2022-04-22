#!/usr/bin/env python
# coding: utf-8

# Import Necessary Modules
import pandas as pd, datetime as dt
import telegram
from kiteconnect import KiteConnect
from os import path

# Get Necessary Parameters
fpath = '/home/ec2-user/algo_trading'

# Telegram Parameters
TOKEN = '5127219747:AAF658kVRmn89YK2Y2Qew8H5INm4_VWitPk'
#chat_id = 573007854
chat_id = 1552723447

# initialising the bot
bot = telegram.Bot(TOKEN)

"""Fetch Orders and Save Data"""
try:

    # Generate Trading Session
    access_token = open(f"{fpath}/auth/data/access_token.txt",'r').read()
    key_secret = open(f"{fpath}/auth/data/api_key.txt",'r').read().split()
    kite = KiteConnect(api_key=key_secret[0])
    kite.set_access_token(access_token)

    # Get Order Details
    col_list = ['order_id', 'order_timestamp', 'tradingsymbol', 'quantity', 'average_price', 'status', 'transaction_type']
    curr_orders_df = pd.DataFrame(kite.orders())[col_list]

    # Read, Append and Save Data
    if path.exists(f"{fpath}/orders_df.csv"):
        orders_df = pd.read_csv(f"{fpath}/orders_df.csv")
        orders_df = orders_df.append(curr_orders_df)
    else:
        orders_df = curr_orders_df.copy()

    # Save Data
    orders_df.to_csv(f"{fpath}/orders_df.csv", index=False)
    
    # Send Message over Telegram
    #bot.send_message(chat_id, f"{dt.datetime.now().date()}\nOrders Data Extracted. {curr_orders_df.index.size} Orders Placed Today.")
    
except Exception as err:
    bot.send_message(chat_id, f"{dt.datetime.now().date()}\nOrders Data Extraction Failed with Error Message: {err}")
