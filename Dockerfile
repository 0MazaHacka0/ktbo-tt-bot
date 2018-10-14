FROM python:3
ADD * /bot/
RUN pip install -r /bot/requirements.txt
CMD [ "cd", "/bot/" ]
CMD [ "python", "./bot/bot.py" ]