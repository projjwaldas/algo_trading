#!/usr/bin/env python
# coding: utf-8

# Import Modules
from kiteconnect import KiteConnect
import time, os, telegram, logging, sys
import pandas as pd, numpy as np
import datetime as dt, math

import bnfStraddleConfig as cfg
sys.path.append('/home/ec2-user/algo_trading')
from NaiveTrader.kite import *
from NaiveTrader.bnf_short_straddle import *
from NaiveTrader.communicate import *

# Get Parameters
fpath = cfg.fpath                           # Program Path
auth_path = cfg.auth_path                   # Access Token File Path
TOKEN = cfg.telegram_TOKEN                  # Telegram Token
chat_id = cfg.chat_id                       # Telegram Chat ID
sl_pct = cfg.sl_pct                         # Stop-Loss %
lot_size = cfg.lot_size                     # Lot Size
bnf_open_time = cfg.bnf_open_time           # BNF Straddle Opening Time
bnf_close_time = cfg.bnf_close_time         # BNF Straddle Closing Time
bnf_index = cfg.bnf_index                   # BNF Index - Options/ Futures

# Derived Parameters
sell_qty = 25*int(lot_size)

# Compute BNF Straddle Close Time
today = dt.datetime.combine(dt.date.today(), dt.datetime.min.time())

bnf_open_min = int(bnf_open_time.split(':')[0])*60 + int(bnf_open_time.split(':')[1]) - 330
straddle_open_time = today+dt.timedelta(minutes=bnf_open_min)

bnf_close_min = int(bnf_close_time.split(':')[0])*60 + int(bnf_close_time.split(':')[1]) - 330
straddle_close_time = today+dt.timedelta(minutes=bnf_close_min)

# Initialise the Bot
bot = telegram.Bot(TOKEN)
