FROM python:3.7

RUN mkdir -p /app
ADD requirements.txt /app
RUN pip install -r /app/requirements.txt -i https://mirrors.aliyun.com/pypi/simple

WORKDIR /app
