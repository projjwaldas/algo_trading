#!/usr/bin/env python
# coding: utf-8

# In[1]:

# Import Libraries & Parameters
import os
# location = os.path.dirname(__file__)
location = '/home/ec2-user/algo_trading/bnf_straddle'
os.chdir(location)
import bnfStraddleConfig as cfg
exec(open('bnf_straddle_module_imports.py').read())

# In[ ]:

# Declare log File
log = f"{fpath}/log/{os.path.basename(__file__).split('.')[0]}.log"
logging.basicConfig(filename=log, level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
logging.getLogger("KiteConnect").setLevel(logging.ERROR)
logging.getLogger("telegram").setLevel(logging.ERROR)
logging.info("********************** Bank Nifty Straddle Hourly PnL Computation Script Started **********************")

# Exit if NSE Holiday
if get_nse_holiday_ind(f"{auth_path}/nse_holiday_list.csv"):
    logging.info(f"{dt.datetime.now().date()} is a holiday")
    #bot.send_message(chat_id, f"{dt.datetime.now().date()} is a holiday")
    sys.exit()

start_time = time.time()

# In[2]:

# Generate Trading Session
kite = connect_kite(auth_path)
logging.info("Kite Connection Established")

# In[6]:

# Check if both the call and put orders have been squared off
orders_df = pd.DataFrame(kite.orders())
pending_orders_df = orders_df[(orders_df['status'] == 'TRIGGER PENDING') & (orders_df['exchange'] == 'NFO')]

# In[8]:

# Fetch Intraday Positions
bnf_sell_df = pd.DataFrame(kite.positions()['day'])
bnf_sell_df = bnf_sell_df[(bnf_sell_df['exchange'] == 'NFO') & 
                          (bnf_sell_df['tradingsymbol'].str.startswith('BANKNIFTY'))][['tradingsymbol', 'pnl', 'sell_price', 'sell_quantity']]
logging.info(f"Pending SL Orders: {pending_orders_df.index.size}")

# In[ ]:

# Compute PnL
if (pending_orders_df.index.size > 0) & (dt.datetime.now() > straddle_open_time) & (dt.datetime.now() < straddle_close_time):

    bnf_sell_df['inv_amt'] = bnf_sell_df['sell_price']*bnf_sell_df['sell_quantity']
    holding = bnf_sell_df[bnf_sell_df['sell_quantity'] > 0].index.size
    logging.info(f"BNF Holding Count: {holding}")
    if (holding > 0):
        #bot.send_message(chat_id, f"Straddle PnL: {np.round(bnf_sell_df['pnl'].sum(), 2)}\nStraddle ROI: {np.round((bnf_sell_df['pnl'].sum()/bnf_sell_df['inv_amt'].sum())*100,2)}%")
        send_telegram_msg(bot, chat_id, f"Straddle PnL: {np.round(bnf_sell_df['pnl'].sum(), 2)}\nStraddle ROI: {np.round((bnf_sell_df['pnl'].sum()/bnf_sell_df['inv_amt'].sum())*100,2)}%")
        logging.info(f"Straddle PnL: {np.round(bnf_sell_df['pnl'].sum(), 2)}\nStraddle ROI: {np.round((bnf_sell_df['pnl'].sum()/bnf_sell_df['inv_amt'].sum())*100,2)}%")


logging.info("**********************Time taken: {(time.time()-start_time)} Seconds**********************\n\n")

