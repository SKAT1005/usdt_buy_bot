FROM python:3.12-bullseye

WORKDIR /app/

RUN apt update

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY bot main.py manage.py run.sh ./
COPY USDT_Buy_Bot ./USDT_Buy_Bot
COPY bot ./bot
RUN chmod +x ./run.sh

ENV BOT_API="test"
ENV RUN_ADMIN="false"

EXPOSE 8000

CMD [ "sh", "-c", "./run.sh" ]