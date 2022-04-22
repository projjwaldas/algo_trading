#!/usr/bin/env python
# coding: utf-8

# Import Modules
from kiteconnect import KiteConnect
import time, telegram, os, os.path, logging, sys
import numpy as np, pandas as pd, datetime as dt

os.chdir('/home/ec2-user/algo_trading/auth')
import authConfig as cfg
sys.path.append('/home/ec2-user/algo_trading')
from NaiveTrader.kite import kite_auth_connect, get_nse_holiday_ind
from NaiveTrader.communicate import send_telegram_msg

# Get Parameters
wpath = cfg.wpath                           # Program Path
fpath = cfg.fpath                           # Data Path
TOKEN = cfg.telegram_TOKEN                  # Telegram Token
chat_id = cfg.chat_id                       # Telegram Chat ID

# Read API Key File
key_secret = open(f"{fpath}/api_key.txt",'r').read().split()

# Declare log File
filename = os.path.basename(__file__)
log = f"{fpath}/{filename.split('.')[0]}.log"
logging.basicConfig(filename=log, level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
logging.getLogger("KiteConnect").setLevel(logging.ERROR)
logging.getLogger("telegram").setLevel(logging.ERROR)
logging.info("**********************Authorisation Script Starts**********************")

# Initialise the Bot
bot = telegram.Bot(TOKEN)

# Exit if NSE Holiday
if get_nse_holiday_ind(f"{fpath}/nse_holiday_list.csv"):
    logging.info(f"{dt.datetime.now().date()} is a holiday")
    send_telegram_msg(bot, chat_id, f"{dt.datetime.now().date()} is a holiday")
    sys.exit()

# Check if Access Token has been updated today
mod_time = time.ctime(os.path.getmtime(f"{fpath}/access_token.txt"))
logging.info(f"Authorisation File Update Date: {dt.datetime.strptime(mod_time, '%c').date()}")
if dt.datetime.strptime(mod_time, "%c").date() != dt.datetime.now().date():
    
    kite_connect_obj = None
    while kite_connect_obj is None:
        try:
            # Generate Request Token
            logging.info("Trying Autologin")
            request_token = kite_auth_connect("/usr/bin/chromedriver", f"{fpath}/api_key.txt")
            logging.info(request_token)
            # Generate and Store Access Token - valid till 6 am the next day
            kite = KiteConnect(api_key=key_secret[0])
            kite_connect_obj = kite.generate_session(request_token, api_secret=key_secret[1])
            with open(f'{fpath}/access_token.txt', 'w') as file:
                file.write(kite_connect_obj["access_token"])
        except:
            time.sleep(10)

    # Send Telegram Message
    margin = np.round(kite.margins('equity')['net'],0) 
    logging.info(f"{dt.datetime.now().date()}\nAccess Token Generation Successful.\nAvailable Kite Margin {margin}")
    #bot.send_message(chat_id, f"{dt.datetime.now().date()}\nAccess Token Generation Successful.\nAvailable Kite Margin {margin}")
    send_telegram_msg(bot, chat_id, f"{dt.datetime.now().date()}\nAccess Token Generation Successful.\nAvailable Kite Margin {margin}")
