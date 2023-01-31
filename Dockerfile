FROM python:3.11

ENV IS_DOCKER Yes

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

WORKDIR /data

ENTRYPOINT [ "python3", "/app/befake.py"]