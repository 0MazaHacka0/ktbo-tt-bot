FROM python:3
ADD * /bot
RUN pip install -r requirements.txt
CMD [ "python", "./bot/bot.py" ]