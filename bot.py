import config

from telegram.ext import CommandHandler, Updater

import requests
from bs4 import BeautifulSoup
import re
from SQLighter import SQLighter
import datetime
import logging


class Parser:
    def __init__(self, url):
        self.url = url

        # Get html
        r = requests.get(self.url)

        # Fix it
        self.html = BeautifulSoup(self.html_fixer(r.content.decode("windows-1251")), "html.parser")

    def parse_groups(self):
        groups = list()

        # Get list of groups
        raw = self.html.find_all("a", attrs={"href": True})

        # Parse groups
        for group in raw:
            name = group.text
            url = config.TIMETABLE_BASE_URL + group.attrs['href']
            if name and url:
                groups.append(Group(name, url))

        return groups

    def parse_timetable(self):

        # Get tables
        tables = self.html.find_all("table")

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

                date = self.parse_date(columns[0].text)
                days.append(Day(date, lessons))

        return days

    def parse_date(self, date_str):
        months = {
            "января": 1,
            "февраля": 2,
            "марта": 3,
            "апреля": 4,
            "мая": 5,
            "июня": 6,
            "июля": 7,
            "августа": 8,
            "сентября": 9,
            "октября": 10,
            "ноября": 11,
            "декабя": 12
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

    def html_fixer(self, page):
        page = page.replace("--!>", "-->")
        page = re.sub('<[/]?B>', "", page)
        page = re.sub('<[/]?I>', "", page)
        page = re.sub('<[/]?FONT.*?>', "", page)
        page = re.sub("<[/]?P.*?>", "", page)
        return page


class Date:
    def __init__(self, week_day, day, month):
        self.week_day = week_day
        self.day = day
        self.month = month


class Group:
    def __init__(self, name, url):
        self.name = name
        self.url = url


class Timetable:
    def __init__(self, weeks):
        self.weeks = weeks


class Week:
    def __init__(self, days):
        self.days = days


class Day:
    def __init__(self, date, lessons):
        self.date = date
        self.lessons = lessons

    def to_string(self):
        string = ""
        for lesson in self.lessons:
            string += lesson.to_string() + "\n"
        return string


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


class Bot:

    def __init__(self):
        pass

    def help(self, bot, update):
        update.message.reply_text('''
    /help - shows help
    /select %group_name% - select group
    /groups - shows list of available groups
    /today - shows today timetable
    /tomorrow - shows tomorrow timetable
        ''')

    def start(self, bot, update):
        bot.send_message(chat_id=update.message.chat.id,
                         text="Hi! Here we list of available groups. Select your :)")

        group_list = ""
        groups = Parser(config.GROUPS_LIST_URL).parse_groups()
        for group in groups:
            group_list += group.name + "\n"

        bot.send_message(chat_id=update.message.chat.id,
                         text=group_list)

    def select_group(self, bot, update, args):
        if len(args) < 1:
            bot.send_message(chat_id=update.message.chat.id,
                             text="Please write after command group name you want to select")
            return

        groups = Parser(config.GROUPS_LIST_URL).parse_groups()

        for group in groups:
            if group.name.lower() == args[0].lower():
                bot.send_message(chat_id=update.message.chat.id,
                                 text="You selected {} group.".format(group.name))
                db.save_group(update.message.chat.id, update.message.chat.username, group.name.lower())
                return

        bot.send_message(chat_id=update.message.chat.id,
                         text="Sorry. I can't find this group")

    def show_tt(self, bot, update, date, group_name=""):

        # Check if user exists in user table
        if not db.check_user(update.message.chat.id) and not (group_name == ""):
            bot.send_message(chat_id=update.message.chat.id,
                             text="Sorry, Dave, I can't do it for you. You don't select your group."
                                  "Use /groups and /select commands")
            return

        # Get group
        if group_name == "":
            group_name = db.get_group(update.message.chat.id)

        bot.send_message(chat_id=update.message.chat.id,
                         text="Day: {0}, Month: {1}, Group: {}".format(date.day, date.month, group_name))

        timetable = list()

        for group in Parser(config.GROUPS_LIST_URL).parse_groups():
            if group.name.lower() == group_name:
                timetable = Parser(group.url).parse_timetable()

                # Find out day
                for day in timetable:
                    if day.date.month == date.month and day.date.day == date.day:
                        bot.send_message(chat_id=update.message.chat.id,
                                         text=day.to_string())
                        return

        bot.send_message(chat_id=update.message.chat.id,
                         text="TT not found")

    def show_today_tt(self, bot, update, args):
        now = datetime.datetime.now()
        day = now.day
        month = now.month

        # Logger
        print("User {0} requested TT for today".format(update.message.chat.first_name))

        if len(args) > 0:
            self.show_tt(bot, update, Date("", day, month), args)
        else:
            self.show_tt(bot, update, Date("", day, month))

    def show_tomorrow_tt(self, bot, update, args):
        now = datetime.datetime.now()
        day = now.day + 1
        month = now.month

        # Logger
        print("User {0} requested TT for tomorrow".format(update.message.chat.first_name))

        if len(args) > 0:
            self.show_tt(bot, update, Date("", day, month), args)
        else:
            self.show_tt(bot, update, Date("", day, month))


# Connect to Telegram
updater = Updater(config.TOKEN)

# Configure logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Configure Telegram Bot
job_updater = updater.job_queue
dispatcher = updater.dispatcher

# Config DB
db = SQLighter(config.DB_NAME)

# List of subscribers
subscribers = set()

# List of users
users = list()

# Timetable
timetable = list()

# Handlers
dispatcher.add_handler(CommandHandler('help', Bot().help))
dispatcher.add_handler(CommandHandler(['start', 'groups'], Bot().start))

# Select group
dispatcher.add_handler(CommandHandler('select', Bot().select_group, pass_args=True))

dispatcher.add_handler(CommandHandler('today', Bot().show_today_tt, pass_args=True))
dispatcher.add_handler(CommandHandler('tomorrow', Bot().show_tomorrow_tt, pass_args=True))

if __name__ == '__main__':
    updater.start_polling()
