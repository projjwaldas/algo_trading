#!/usr/bin/env python
# coding: utf-8

# In[1]:

# Import Libraries & Parameters
import os
#location = os.path.dirname(__file__)
os.chdir('/home/ec2-user/algo_trading/bnf_straddle')
import bnfStraddleConfig as cfg
exec(open('bnf_straddle_module_imports.py').read())

# Declare log File
log = f"{fpath}/log/{os.path.basename(__file__).split('.')[0]}.log"
logging.basicConfig(filename=log, level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
logging.getLogger("KiteConnect").setLevel(logging.ERROR)
logging.getLogger("telegram").setLevel(logging.ERROR)
logging.info("**********************Bank Nifty Straddle Sell Script Started.**********************")

# Exit if NSE Holiday
if get_nse_holiday_ind(f"{auth_path}/nse_holiday_list.csv"):
    logging.info(f"{dt.datetime.now().date()} is a holiday")
    #bot.send_message(chat_id, f"{dt.datetime.now().date()} is a holiday")
    sys.exit()

# Record Script Start time
start_time = time.time()

# In[2]:

try:
    # Generate Trading Session
    kite = connect_kite(auth_path)
    logging.info("Kite Connection Established")

    # Get BNF Spot Price
    bnf_token = get_bnf_token(kite, bnf_index)
    bnf_spot_price = kite.quote(bnf_token)[f'{bnf_token}']['last_price']
    logging.info(f"BNF Future Spot Price: {bnf_spot_price}")

    # Get Bank Nifty Call and Put Options to Buy and Price
    atm_price, bnf_straddle_df = get_bnf_token_prc(kite, bnf_spot_price)
    bnf_straddle_df['sl'] = bnf_straddle_df['instrument_token'].apply(lambda x: math.floor(kite.quote(x)[f'{x}']['last_price']*(1+sl_pct)))
    #bnf_straddle_df['sl'] = bnf_straddle_df['last_price'].apply(lambda x: math.floor(x*(1+sl_pct)))

    logging.info(f"ATM Price: {atm_price}")
    logging.info(f"Call Option Token: {bnf_straddle_df.loc[bnf_straddle_df['instrument_type']=='CE', 'tradingsymbol'].values[0]}")
    logging.info(f"Put Option Token: {bnf_straddle_df.loc[bnf_straddle_df['instrument_type']=='PE', 'tradingsymbol'].values[0]}")

# In[4]:

    # Order Placement
    bnf_orders_df = pd.DataFrame()
    i = 0
    while (bnf_orders_df.index.size == 0) & (i < 4):
        i += 1 
        try:
            # Place Orders
            logging.info("Placing Orders")
            bnf_straddle_df.apply(lambda row: placeSLOrder(kite, row['tradingsymbol'], 'sell', sell_qty, row['sl']), axis=1)
            # bnf_straddle_df.apply(lambda row: PlaceStradleOrder(kite, row['tradingsymbol'], sell_qty), axis=1)
            bnf_straddle_df.apply(lambda row: logging.info(f"BNF Straddle Orders Placed: (Symbol: {row['tradingsymbol']}, Quantity: {sell_qty})"), axis=1)
            time.sleep(5)
        
            # Fetch Recent Orders
            bnf_orders_df = get_bnf_orders(kite)
#            bnf_orders_df = bnf_orders_df[(bnf_orders_df['status'] == 'COMPLETE') & (bnf_orders_df['transaction_type'] == 'SELL')]
            bnf_orders_df = bnf_orders_df[(bnf_orders_df['status'] == 'COMPLETE') & (bnf_orders_df['transaction_type'] == 'SELL') &
                                          (bnf_orders_df['order_timestamp'] + dt.timedelta(minutes=1) >= dt.datetime.now() + dt.timedelta(minutes=330))]
            bnf_orders_df['inv_amt'] = bnf_orders_df['average_price'] * bnf_orders_df['quantity']
            bnf_orders_df['sl'] = bnf_orders_df['average_price'].apply(lambda x: x*(1+sl_pct))

            # Send Telegram Message
            org_msg = f'{dt.datetime.now().date()}\nFuture Spot Price: {bnf_spot_price}\n'
            for i in range(bnf_orders_df.index.size):
                msg = f"Sell {bnf_orders_df.iloc[i]['tradingsymbol']} at {np.round(bnf_orders_df.iloc[i]['average_price'], 1)} (SL {np.round(bnf_orders_df.iloc[i]['sl'], 1)})"
                org_msg = org_msg + '\n' + msg
            org_msg = org_msg + f"\n\nLot Size: {lot_size}\nPremium Amount: {np.round(bnf_orders_df['inv_amt'].sum(), 2)}\nTotal Investment Amount: {np.round(kite.margins()['equity']['utilised']['debits'], 2)}"
            send_telegram_msg(bot, chat_id, org_msg)

            logging.info(f"Total Invested Amount: {np.round(bnf_orders_df['inv_amt'].sum())}")
            logging.info(f"**********************Time taken: {(time.time()-start_time)} Seconds**********************\n\n")
            break

        except:
            time.sleep(2)

except Exception as err:
    send_telegram_msg(bot, chat_id, f"BNF Straddle Sell Script failed with error message: {err}")
    logging.exception("Exception occurred", exc_info=True)
