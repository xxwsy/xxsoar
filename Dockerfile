FROM python:3.7-alpine

RUN mkdir -p /app
ADD . /app
RUN pip install -r /app/requirements.txt -i https://mirrors.aliyun.com/pypi/simple

WORKDIR /app
