import config
from telegram.ext import CommandHandler, Updater
import requests
from bs4 import BeautifulSoup
import re
from SQLighter import SQLighter
import datetime


class Date:
    def __init__(self, week_day, day, month):
        self.week_day = week_day
        self.day = day
        self.month = month


class Lesson:
    def __init__(self, name, teacherName, classroomName):
        self.name = name
        self.teacherName = teacherName
        self.classroomName = classroomName


class Day:
    def __init__(self, date, lessons):
        self.date = date
        self.lessons = lessons


class Week:
    def __init__(self, days):
        self.days = days


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

# Fix bugs in html
def fixer(page):
    page = \
        page\
        .replace("--!>", "-->")\
        .replace("<I>", "")\
        .replace("</I>", "")\
        .replace("<B>", "")\
        .replace("</B>", "")\
        .replace("</P>", "")\

    page = re.sub('<[/]?FONT.*?>', "", page)
    page = re.sub("<[/]?P.*?>", "", page)
    return page


def parse_date(date_str):
    months = {
        "сентября": 9
    }
    days_week = {
        "Пнд": 1,
        "Втр": 2,
        "Срд": 2,
        "Чтв": 2,
        "Птн": 2,
        "Сбт": 2,

    }
    date_str = date_str.replace(',', ' ').strip().split(' ')
    return Date(days_week[date_str[0]], int(date_str[1]), months[date_str[3]])


def parse():
    r = requests.get(config.UFO_URL)

    with open("index.html", "w") as file:
        file.write(fixer(r.content.decode("windows-1251")))

    html = BeautifulSoup(fixer(r.content.decode("windows-1251")), "html.parser")

    # Get tables
    tables = html.find_all("table")

    days = list()

    # For each table find lines
    for table in tables:
        lines = table.find_all("tr")

        # For each line find columns
        # Skipping first two lines
        for line in lines[2::]:
            columns = line.find_all("td")
            lessons = list()

            # For all columns print text
            for column in columns[1::]:
                lessons.append(Lesson(column.text, "", ""))

            date = parse_date(columns[0].text)
            days.append(Day(date, lessons))

    return days

days = parse()


def show_today_tt(bot, update):
    now = datetime.datetime.now()

    bot.send_message(chat_id=update.message.chat.id, text="Day: {0}, Month: {1}".format(now.day, now.month))

    # Find out day
    flag = False
    for day in days:
        if day.date.month == now.month and day.date.day == now.day + 1:
            tt = ""
            for lesson in day.lessons:
                tt += lesson.name + "\n"
            bot.send_message(chat_id=update.message.chat.id,
                             text=tt)
            flag = True
            break

    if not flag:
        bot.send_message(chat_id=update.message.chat.id,
                             text="TT not found")



# Handlers
dispatcher.add_handler(CommandHandler('today', show_today_tt))

if __name__ == '__main__':
    updater.start_polling()