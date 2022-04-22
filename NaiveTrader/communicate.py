#!/usr/bin/env python
# coding: utf-8
"""
- Send Telegram Messages to Multiple Chat ID's  
"""

# Import Modules
import telegram

def send_telegram_msg(bot, chat_id, msg):
    """
    Parameters
    ----------
        bot: python telegram bot object
        chat_id: list or str, chat id
        msg: str, Message that needs to be sent to the telegram chat
    Returns
    -------
        sends the message to the telegram chat id(s)
    """
    if not isinstance(chat_id, list):
        chat_id = [chat_id]
    for id in chat_id:
        bot.send_message(id, msg)
