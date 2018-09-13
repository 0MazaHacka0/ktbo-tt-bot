import config
from telegram.ext import CommandHandler, Updater
import requests

from SQLighter import SQLighter

# Connect to Telegram
updater = Updater(config.TOKEN)

# Configure Telegram Bot
job_updater = updater.job_queue
dispatcher = updater.dispatcher

# Config DB
db = SQLighter('db.sqlite')

# List of subscribers
subscribers = set()

# Timetable
timetable = list()

# Define commands
def getTimeTable():
	r = request


def today(bot, update):
	

def tomorrow():
