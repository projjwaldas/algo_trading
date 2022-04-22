#!/usr/bin/env python
# coding: utf-8
"""
- Get BNF Straddle Orders, Positions & PnL  
- Place intraday buy & sell order for options  
- Place intraday SL order for options 
"""

# Import Modules
import pandas as pd, numpy as np
from kiteconnect import KiteConnect
import pyotp, time
import datetime as dt

from .kite import get_positions, get_orders


def get_bnf_straddle_positions(kite):
    """
    Parameters
    ----------
        kite: kite object
    Returns
    -------
        pandas dataframe of Bank Nifty Options positions
    """
    pos_df = get_positions(kite)
    bnf_pos_df = pos_df[(pos_df['exchange'] == 'NFO') & (pos_df['tradingsymbol'].str.startswith('BANKNIFTY'))]
    return(bnf_pos_df)


def get_bnf_orders(kite):
    """
    Parameters
    ----------
        kite: kite object
    Returns
    -------
        pandas dataframe of Bank Nifty options orders
    """
    orders_df = get_orders(kite)
    bnf_orders_df = orders_df[(orders_df['exchange'] == 'NFO') & (orders_df['tradingsymbol'].str.startswith('BANKNIFTY'))]
    return(bnf_orders_df)


def get_bnf_straddle_holdings(kite):
    """
    Parameters
    ----------
        kite: kite object
    Returns
    -------
        pandas dataframe of Bank Nifty Holdings
    """
    pos_df = get_bnf_straddle_positions(kite)
    holding_df = pos_df[pos_df['buy_quantity'] == 0]
    return(holding_df)


def calc_bnf_straddle_pnl(kite, pnl_fname):
    """
    Parameters
    ----------
        kite: kite object
    Returns
    -------
        pandas dataframe of Bank Nifty short straddle PnL
    """
    # Get Today's Intraday Positions
    bnf_pos_df = get_bnf_straddle_positions(kite)

    # Calculate Charges
    bnf_pos_df['brokerage'] = 40
    bnf_pos_df['stt'] = bnf_pos_df['sell_value']*0.0005
    bnf_pos_df['nse_charge'] = bnf_pos_df['buy_value']*0.00053
    bnf_pos_df['gst'] = (bnf_pos_df['nse_charge']+bnf_pos_df['brokerage'])*0.18
    bnf_pos_df['sebi_charge'] = (bnf_pos_df['buy_value']+bnf_pos_df['sell_value'])*10/10000000
    bnf_pos_df['stamp_charge'] = bnf_pos_df['buy_value']*0.00003
    bnf_pos_df['total_charge'] = bnf_pos_df[['brokerage', 'stt', 'nse_charge', 'gst', 'sebi_charge', 'stamp_charge']].sum(axis=1)
    bnf_pos_df['net_pnl'] = bnf_pos_df['pnl'] - bnf_pos_df['total_charge']

    # Keep only Required Columns
    keep_col_list = ['tradingsymbol', 'instrument_token', 'pnl', 'buy_quantity', 'buy_price', 'buy_value', 'sell_quantity', 'sell_price', 'sell_value', 'total_charge', 'net_pnl']
    bnf_pos_df = bnf_pos_df[keep_col_list]
    bnf_pos_df['date'] = dt.datetime.now().date()

    # Save PnL Data
    try:
        pnl_df = pd.read_csv(pnl_fname)
        pnl_df = pnl_df.append(bnf_pos_df)
        pnl_df.to_csv(pnl_fname, index=False)
    except:
        bnf_pos_df.to_csv(pnl_fname, index=False)
        
    return(bnf_pos_df)


def get_bnf_indices(kite):
    """
    Parameters
    ----------
        kite: kite object
    Returns
    -------
        returns Bank Nifty Index token
    """
    # Get Bank Nifty Instrument
    instruments_df = pd.DataFrame(kite.instruments(kite.EXCHANGE_NSE))
    bnf_df = instruments_df[(instruments_df['tradingsymbol'] == 'NIFTY BANK')]

    # Get Token
    bnf_token = bnf_df['instrument_token'].values[0]
    return(bnf_token)


def get_bnf_fut(kite):
    """
    Parameters
    ----------
        kite: kite object
    Returns
    -------
        returns Bank Nifty Future with current month expiry token
    """
    # Get All Instruments
    instruments_df = pd.DataFrame(kite.instruments(exchange=kite.EXCHANGE_NFO))
    instruments_df['expiry'] = pd.to_datetime(instruments_df['expiry'], format='%Y-%m-%d')

    # Get All Banknifty Future Instruments
    bnf_instruments_df = instruments_df[(instruments_df['name'].str.contains('BANKNIFTY'))]
    fut_instruments_df = bnf_instruments_df[(bnf_instruments_df['segment'].isin(['NFO-FUT']))]
    bnf_fut_df = fut_instruments_df[fut_instruments_df['expiry'] == min(fut_instruments_df['expiry'])]
    bnf_fut_token = bnf_fut_df['instrument_token'].values[0]
    return(bnf_fut_token)

def get_bnf_token(kite, index):
    """
    Parameters
    ----------
        kite: kite object
        index: str, whether bank nifty straddle will be based on Options or Futures
    Returns
    -------
        returns token of the Bank Nifty spot ATM
    """
    if index == 'OPT':
        return(get_bnf_indices(kite))
    elif index == 'FUT':
        return(get_bnf_fut(kite))
    
    
def get_bnf_token_prc(kite, spot_prc):
    """
    Parameters
    ----------
        kite: kite object
    Returns
    -------
        Identifies the BNF ATM price, and the token & prices of the BNF CE/ PE ATM
    """
    # Get All Banknifty Option Weekly Expiry Instruments
    instruments_df = pd.DataFrame(kite.instruments(exchange=kite.EXCHANGE_NFO))
    instruments_df['expiry'] = pd.to_datetime(instruments_df['expiry'], format='%Y-%m-%d')

    opt_instruments_df = instruments_df[(instruments_df['name'].str.contains('BANKNIFTY')) & (instruments_df['segment'] == 'NFO-OPT')]
    bnf_option_weekly_expiry_df = opt_instruments_df[opt_instruments_df['expiry'] == min(opt_instruments_df['expiry'])]

    # Identify ATM Price
    strike_list = list(bnf_option_weekly_expiry_df['strike'].drop_duplicates())
    atm_price = min(strike_list, key=lambda u:abs(u-spot_prc))
    bnf_option_atm_df = bnf_option_weekly_expiry_df[bnf_option_weekly_expiry_df['strike'] == atm_price]

    return(atm_price, bnf_option_atm_df)


# Place an intraday Buy Order on NSE Options
def ExitStradleOrder(kite, symbol, quantity):
    """
    Parameters
    ----------
        kite: kite object
        symbol: str, symbol of options instrument
        quantity: int, quantity of stock in units
    Returns
    -------
        places intraday buy order for options instrument on Zerodha Kite
    """
    kite.place_order(tradingsymbol=symbol,
        exchange=kite.EXCHANGE_NFO,
        transaction_type=kite.TRANSACTION_TYPE_BUY,
        quantity=quantity,
        order_type=kite.ORDER_TYPE_MARKET,
        product=kite.PRODUCT_MIS,
        variety=kite.VARIETY_REGULAR)

# Place an Intraday Sell Order on NSE Options
def PlaceStradleOrder(kite, symbol, quantity):
    """
    Parameters
    ----------
        kite: kite object
        symbol: str, symbol of options instrument
        quantity: int, quantity of stocks in units
    Returns
    -------
        places intraday sell order for options instrument on Zerodha Kite
    """
    kite.place_order(tradingsymbol=symbol,
            exchange=kite.EXCHANGE_NFO,
            transaction_type=kite.TRANSACTION_TYPE_SELL,
            quantity=quantity,
            order_type=kite.ORDER_TYPE_MARKET,
            product=kite.PRODUCT_MIS,
            variety=kite.VARIETY_REGULAR)


# Place an intraday Stop loss order on NSE Options
def placeSLOrder(kite, symbol, buy_sell, quantity, sl_price):
    """
    Parameters
    ----------
        kite: kite object
        symbol: str, symbol of options instrument
        buy_sell: str, indicator whether buy or sell order
        quantity: int, quantity of stocks in units
        sl_price: float, SL price
    Returns
    -------
        places intraday SL order for options instrument on Zerodha Kite based on transaction type (buy/ sell)
    """
    if buy_sell == "buy":
        t_type=kite.TRANSACTION_TYPE_BUY
        t_type_sl=kite.TRANSACTION_TYPE_SELL
    elif buy_sell == "sell":
        t_type=kite.TRANSACTION_TYPE_SELL
        t_type_sl=kite.TRANSACTION_TYPE_BUY
    kite.place_order(tradingsymbol=symbol,
            exchange=kite.EXCHANGE_NFO,
            transaction_type=t_type,
            quantity=quantity,
            order_type=kite.ORDER_TYPE_MARKET,
            product=kite.PRODUCT_MIS,
            variety=kite.VARIETY_REGULAR)
    kite.place_order(tradingsymbol=symbol,
            exchange=kite.EXCHANGE_NFO,
            transaction_type=t_type_sl,
            quantity=quantity,
            order_type=kite.ORDER_TYPE_SL,
            price=sl_price,
            trigger_price = sl_price,
            product=kite.PRODUCT_MIS,
            variety=kite.VARIETY_REGULAR)
