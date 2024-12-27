# config.py
import os
from dotenv import load_dotenv


load_dotenv()
BOT_NAME = 'abhishrent'
PREFIX = ('prefix_1 ', 'prefix_2 ')

BOT_TOKEN = os.getenv("BOT_TOKEN")  # This will read from environment variable
if BOT_TOKEN is None:
    raise ValueError("Bot token not found in environment variables. Please check your .env file.")


"""
BOT_TOKEN = 'your token' #replace lines 10 to 12 with this if you don't want to set environment variables.
"""
