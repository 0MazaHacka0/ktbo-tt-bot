FROM python:3
ADD * /bot/
RUN pip install -r /bot/requirements.txt
CMD [ "python", "./bot/bot.py" ]