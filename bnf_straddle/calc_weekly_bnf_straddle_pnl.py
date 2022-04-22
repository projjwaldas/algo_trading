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
log = f'{fpath}/log/calc_weekly_bnf_straddle_pnl.log'
logging.basicConfig(filename=log, level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.info("\n\n******************** BNF Straddle Weekly PnL Calculation Script Started ***************************")

# Record Script Start time
start_time = time.time()

# Get Current Week's Dates
today = dt.datetime.now().date()
week_start = pd.to_datetime(today - dt.timedelta(days=today.weekday()))

logging.info(f"Start of the Week: {week_start}")

# Import Momentum P&L Data
pnl_df = pd.read_csv(f"{fpath}/data/bnf_straddle_pnl_df.csv")
pnl_df['date'] = pd.to_datetime(pnl_df['date'], format='%Y-%m-%d')


# Subset Data for the Current Week
pnl_df = pnl_df[(pnl_df['date'] >= week_start)].drop_duplicates()
pnl_df['pnl_pct'] = pnl_df['pnl']/pnl_df['sell_value']
pnl_df['sl_hit'] = np.where(pnl_df['pnl_pct'] < -0.24, 1, 0)
logging.info(f"PnL Information Imported. Total {pnl_df.index.size} trades.")

# How many Stop-Loss were hit this week?
daily_sl_hit = pnl_df.groupby('date')['sl_hit'].sum().reset_index()
sl_hit_summary = daily_sl_hit.groupby('sl_hit')['date'].count().reset_index()

# Create String for Telegram
weekly_report_str = f"BNF Straddle Weekly Report\n{week_start.date()} - {today}\n\nTotal Weekly PnL: {int(np.round(pnl_df['pnl'].sum(), 0))}\nTotal Weekly Charges: {int(np.round(pnl_df['total_charge'].sum(), 0))}\nNet PnL Post Charges: {int(np.round(pnl_df['net_pnl'].sum(), 0))}\n"

for i in range(sl_hit_summary.index.size):
    msg = f"{sl_hit_summary.iloc[i]['sl_hit']} SL hit: {sl_hit_summary.iloc[i]['date']} days"
    weekly_report_str = weekly_report_str + '\n' + msg

# Send Message
send_telegram_msg(bot, chat_id, weekly_report_str)

# Logging
logging.info(f"Total Weekly PnL: {pnl_df['pnl'].sum()}")
logging.info(f"Total Weekly Charges: {pnl_df['total_charge'].sum()}\nNet PnL Post Charges: {pnl_df['net_pnl'].sum()}")

logging.info(f"**********************Time taken: {(time.time()-start_time)} Seconds********************************")
