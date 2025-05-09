FROM python:3.12.3

RUN apt-get update && \
    apt-get install -y git wget make && \
    apt-get install -y python3-dev python3-pip && \
    python3 -m pip install -U pip

WORKDIR /app

COPY ./src /app
COPY ./requirements.txt /app

RUN python3 -m pip install -r requirements.txt

CMD ["fastapi", "run", "main.py"]
