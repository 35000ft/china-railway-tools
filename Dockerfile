FROM python:3.12.3-bullseye AS china-railway-fastapi

COPY /requirements.txt /app/requirements.txt
RUN pip install uvicorn

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \

FROM china-railway-fastapi
COPY . /app
WORKDIR /app
RUN pip install -r /app/requirements.txt

RUN mkdir -p /app/temp \
    && mkdir -p /app/logs \

EXPOSE 8250

# 定义容器启动时运行的命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8250"]
