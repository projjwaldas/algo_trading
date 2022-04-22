#!/usr/bin/env python
# coding: utf-8
"""
This library provides helper functions for automated trading through python. The trades will be executed through Zerodha Kite API.   
The user needs to have a Zerodha Kite API subscription from https://developers.kite.trade/apps  

1. The API key and API secret, alongwith Zerodha Kite user credentials and TOTP ID will need to be put in a text file (access_token.txt) for the daily request token generation for Zerodha Kite connect.  
2. A chromedriver file will be required to automatically start chrome through selenium web driver for Zerodha Kite connect. The chromedriver file is available for free downlaod @ https://chromedriver.chromium.org/downloads  
Please download the appropriate version depending on chrome version. This needs to be placed at /usr/bin/chromedriver  

The following python libraries will be required:   

 - pandas  
 - numpy  
 - kiteconnect  
 - selenium  
 - pyotp  
 - telegram  
 - datetime  
 - time  

Available Startegies
--------------------
1. Bank Nifty Short Straddle (Version 0.0.1)


Developer
---------
Projjwal Das (projjwal.das@gmail.com)

Version
-------
0.0.1
"""
