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
    def __init__(self, name, teacherName, classroomName, index):
        if name == "\n":
            self.name = "ОКНО"
        else:
            self.name = name
        self.teacherName = teacherName
        self.classroomName = classroomName
        self.index = index


    def get_time(self, index):
        time = {
            1: "08:00-09:35",
            2: "09:50-11:25",
            3: "11:55-13:30",
            4: "13:45-15:20",
            5: "15:50-17:25",
            6: "17:40-19:15",
            7: "19:30-21:05"
        }
        return time[index]


    def to_string(self):
        string = "{0}. {1} {2}".format(self.index, self.get_time(self.index), self.name)
        return string


class Day:
    def __init__(self, date, lessons):
        self.date = date
        self.lessons = lessons

    def to_string(self):
        string = ""
        for lesson in self.lessons:
            string += lesson.to_string() + "\n"
        return string


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
    page = page.replace("--!>", "-->")
    page = re.sub('<[/]?B>', "", page)
    page = re.sub('<[/]?I>', "", page)
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
        "Срд": 3,
        "Чтв": 4,
        "Птн": 5,
        "Сбт": 6,
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
            tmp = 0
            for column in columns[1::]:
                tmp += 1
                lessons.append(Lesson(column.text, "", "", tmp))

            date = parse_date(columns[0].text)
            days.append(Day(date, lessons))

    return days


days = parse()


def help(bot, update):
    update.message.reply_text('''
/help - shows help
/today - shows today timetable
/tomorrow - shows tomorrow timetable
/subscribe - subscribe you to tt updates
/unsubscribe - unsubscribe you from tt updates
    ''')


# Callback send message with new sessions
def update_tt(bot, job):
    global days
    days = parse()
    print("TT updated")


def subscribe(bot, update):
    state = db.subscribe(update.message.chat.id)
    if state is False:
        bot.send_message(chat_id=update.message.chat.id, text='You already subscribed')
    else:
        bot.send_message(chat_id=update.message.chat.id, text='You have successfully subscribed')


def unsubscribe(bot, update):
    state = db.unsubscribe(update.message.chat.id)
    if state is False:
        bot.send_message(chat_id=update.message.chat.id, text='You are not subscribed')
    else:
        bot.send_message(chat_id=update.message.chat.id, text='You have successfully unsubscribed')


def show_tt(bot, update, date):
    bot.send_message(chat_id=update.message.chat.id, text="Day: {0}, Month: {1}".format(date.day, date.month))

    # Find out day
    flag = False
    for day in days:
        if day.date.month == date.month and day.date.day == date.day:
            bot.send_message(chat_id=update.message.chat.id,
                             text=day.to_string())
            flag = True
            break

    if not flag:
        bot.send_message(chat_id=update.message.chat.id,
                         text="TT not found")


def show_today_tt(bot, update):
    now = datetime.datetime.now()
    day = now.day
    month = now.month

    # Logger
    print("User {0} requested TT for today".format(update.message.chat.first_name))

    show_tt(bot, update, Date("", day, month))


def show_tomorrow_tt(bot, update):
    now = datetime.datetime.now()
    day = now.day + 1
    month = now.month

    # Logger
    print("User {0} requested TT for tomorrow".format(update.message.chat.first_name))

    show_tt(bot, update, Date("", day, month))


# Repeatable job queue
job_updater.run_repeating(update_tt, interval=1, first=0)

# Handlers
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(CommandHandler('start', help))

dispatcher.add_handler(CommandHandler('subscribe', subscribe))
dispatcher.add_handler(CommandHandler('unsubscribe', unsubscribe))

dispatcher.add_handler(CommandHandler('today', show_today_tt))
dispatcher.add_handler(CommandHandler('tomorrow', show_tomorrow_tt))

if __name__ == '__main__':
    updater.start_polling()
