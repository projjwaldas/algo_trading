#!/usr/bin/env python
# coding: utf-8

# Import Libraries & Parameters
import os
# location = os.path.dirname(__file__)
location = '/home/ec2-user/algo_trading/bnf_straddle'
os.chdir(location)
import bnfStraddleConfig as cfg
exec(open('bnf_straddle_module_imports.py').read())


# Declare log File
filename = os.path.basename(__file__)
log = f"{fpath}/log/{filename.split('.')[0]}.log"
logging.basicConfig(filename=log, level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
logging.getLogger("KiteConnect").setLevel(logging.ERROR)
logging.getLogger("telegram").setLevel(logging.ERROR)
logging.info("\n\n**********************Bank Nifty Straddle Monitoring Script Started.**********************")

# Exit if NSE Holiday
if get_nse_holiday_ind(f"{auth_path}/nse_holiday_list.csv"):
    logging.info(f"{dt.datetime.now().date()} is a holiday")
    #bot.send_message(chat_id, f"{dt.datetime.now().date()} is a holiday")
    sys.exit()

start_time = time.time()

try:

    # Kill the Program if Current time <= Straddle Open Time
    if (pd.Timestamp(dt.datetime.now()) <= straddle_open_time + dt.timedelta(minutes=1)):
        logging.info("Killing the program")
        sys.exit()

    # Generate Trading Session
    kite = connect_kite(auth_path)
    logging.info("Kite Connection Established")

    # Get Orders, Positions and holdings Data
    bnf_orders_df = get_bnf_orders(kite)
    bnf_pos_df = get_bnf_straddle_positions(kite)
    bnf_holdings_df = get_bnf_straddle_holdings(kite)
    logging.info(f"BNF Straddle Holding: {bnf_holdings_df.index.size}")


    """Check if SL is hit"""

    # Fetch Completed SL Orders
    logging.info(f"\nSL hit computation starts here - Current Datetime: {dt.datetime.now()}")
    sl_order_df = bnf_orders_df[(bnf_orders_df['order_type'] == 'LIMIT') & (bnf_orders_df['status'] == 'COMPLETE') &
                                (bnf_orders_df['order_timestamp'] + dt.timedelta(minutes=2) >= dt.datetime.now() + dt.timedelta(minutes=330))]
    logging.info(f"SL hit for {sl_order_df.index.size} orders")

    # Notify users for placed SL Buy Orders
    if (dt.datetime.now() < straddle_close_time) & (sl_order_df.index.size > 0):

        sl_order_df = sl_order_df[['tradingsymbol', 'price']].merge(bnf_pos_df, on=['tradingsymbol'], how='left')
        sl_order_df.apply(lambda row: send_telegram_msg(bot, chat_id, f"{row['tradingsymbol']} hit Stop-Loss limit @ {row['buy_price']}\n\nPnL: {np.round(row['pnl'], 2)}, ROI: {np.round((row['pnl']/row['sell_value'])*100, 2)}%"), axis=1)
        sl_order_df.apply(lambda row: logging.info(f"{row['tradingsymbol']} hit Stop-Loss limit @ {row['buy_price']}\nPnL: {np.round(row['pnl'], 2)}, ROI: {np.round((row['pnl']/row['sell_value'])*100, 2)}%"), axis=1)

        # Calculate PnL & Charges
        if bnf_holdings_df.index.size == 0:
            bnf_pnl_df = calc_bnf_straddle_pnl(kite, f"{fpath}/data/bnf_straddle_pnl_df.csv")
            send_telegram_msg(bot, chat_id, f"Total Charges Paid: {np.round(bnf_pnl_df['total_charge'].sum(), 2)}\nStraddle PnL post charges: {np.round(bnf_pnl_df['net_pnl'].sum(), 2)}\nStraddle ROI post charges: {np.round((bnf_pnl_df['net_pnl'].sum()/bnf_pnl_df['sell_value'].sum())*100, 2)}%")
            logging.info(f"Total Charges Paid: {np.round(bnf_pnl_df['total_charge'].sum(), 2)}\nStraddle PnL post charges: {np.round(bnf_pnl_df['net_pnl'].sum(), 2)}\nStraddle ROI post charges: {np.round((bnf_pnl_df['net_pnl'].sum()/bnf_pnl_df['sell_value'].sum())*100, 2)}%")


    """If EOD"""

    # Close orders on EOD
    logging.info(f"\nEOD Computation starts here - Current Datetime: {dt.datetime.now()}")
    if (dt.datetime.now() >= straddle_close_time) & (bnf_holdings_df.index.size > 0):

        # Close Orders
        bnf_holdings_df.apply(lambda row: ExitStradleOrder(kite, {row['tradingsymbol']}, {sell_qty}), axis=1)
        pending_sl_order_df = bnf_orders_df[bnf_orders_df['status'] == 'TRIGGER PENDING']
        pending_sl_order_df.apply(lambda row: kite.cancel_order(order_id=row['order_id'], variety='regular'), axis=1)

        # Calculate PnL
        bnf_pos_df = get_bnf_straddle_positions(kite)
        org_msg = f"Closing BNF Straddle \n{(dt.datetime.now() + dt.timedelta(minutes=330)).strftime('%Y-%m-%d %H:%M')}\n\nStraddle PnL: {np.round(bnf_pos_df['pnl'].sum(), 2)}\nStraddle ROI: {np.round((bnf_pos_df['pnl'].sum()/bnf_pos_df['sell_value'].sum())*100, 2)}%\n\n"

        # Calculate PnL & Charges
        bnf_pnl_df = calc_bnf_straddle_pnl(kite, f"{fpath}/data/bnf_straddle_pnl_df.csv")
        org_msg = org_msg + f"Total Charges Paid: {np.round(bnf_pnl_df['total_charge'].sum(), 2)}\nStraddle PnL post charges: {np.round(bnf_pnl_df['net_pnl'].sum(), 2)}\nStraddle ROI post charges: {np.round((bnf_pnl_df['net_pnl'].sum()/bnf_pnl_df['sell_value'].sum())*100, 2)}%"
        send_telegram_msg(bot, chat_id, org_msg)
        logging.info(org_msg)



    """ Manual Exit """

    # Get Recently Closed Orders
    logging.info("\nManual Order Check Computation starts here - Current Datetime: {dt.datetime.now()}")
    bnf_order_df = get_bnf_orders(kite)
    straddle_closing_order_df = bnf_order_df[(bnf_order_df['status'] == 'COMPLETE') & (bnf_order_df['transaction_type'] == 'BUY') &
                                             (bnf_order_df['order_timestamp'] >= dt.datetime.now()+dt.timedelta(minutes=330)-dt.timedelta(minutes=2))]
    logging.info(f"Recently closed orders: {straddle_closing_order_df.index.size}")

    if (dt.datetime.now() < straddle_close_time) & (bnf_holdings_df.index.size == 0) & (sl_order_df.index.size == 0) & (straddle_closing_order_df.index.size > 0):
        # Close Stop-Loss Orders
        orders_df = get_bnf_orders(kite)
        pending_sl_order_df = orders_df[orders_df['status'] == 'TRIGGER PENDING']
        pending_sl_order_df.apply(lambda row: kite.cancel_order(order_id=row['order_id'], variety='regular'), axis=1)
        pending_sl_order_df.apply(lambda row: logging.info(f"kite.cancel_order(order_id={row['order_id']}, variety='regular')"), axis=1)

        # Compute pnl and Send Message
        org_msg = f"Manual Straddle Exit\n{(dt.datetime.now() + dt.timedelta(minutes=330)).strftime('%Y-%m-%d %H:%M')}\n\n"
        manual_close_df = bnf_pos_df[bnf_pos_df['tradingsymbol'].isin(straddle_closing_order_df['tradingsymbol'])]
        for i in range(manual_close_df.index.size):
            org_msg = org_msg + f"Manual Exit {manual_close_df.iloc[i]['tradingsymbol']} (Pnl: {np.round(manual_close_df.iloc[i]['pnl'], 2)}, ROI: {np.round((manual_close_df.iloc[i]['pnl']/manual_close_df.iloc[i]['sell_value'])*100, 2)}%)\n"
        org_msg = org_msg + f"\nStraddle PnL: {np.round(bnf_pos_df['pnl'].sum(), 2)}\nStraddle ROI: {np.round((bnf_pos_df['pnl'].sum()/bnf_pos_df['sell_value'].sum())*100, 2)}%"  
    
        # Calculate PnL & Charges
        bnf_pnl_df = calc_bnf_straddle_pnl(kite, f"{fpath}/data/bnf_straddle_pnl_df.csv")
        org_msg = org_msg + f"\n\nTotal Charges Paid: {np.round(bnf_pnl_df['total_charge'].sum(), 2)}\nStraddle PnL post charges: {np.round(bnf_pnl_df['net_pnl'].sum(), 2)}\nStraddle ROI post charges: {np.round((bnf_pnl_df['net_pnl'].sum()/bnf_pnl_df['sell_value'].sum())*100, 2)}%"
        send_telegram_msg(bot, chat_id, org_msg)
        logging.info(org_msg)


    logging.info(f"**********************Time taken: {(time.time()-start_time)} Seconds**********************")

except Exception as err:
    #if (dt.datetime.now() > today+dt.timedelta(minutes=240):
    #bot.send_message(chat_id, f"BNF Straddle Monitoring Script failed with error message: {err}")
    send_telegram_msg(bot, chat_id, f"BNF Straddle Monitoring Script failed with error message: {err}")
    logging.exception("Exception occurred", exc_info=True)
