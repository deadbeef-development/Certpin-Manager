FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y nginx && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/certpin

COPY manager.py .
COPY requirements.txt .

RUN python3 -m pip install --no-cache-dir -r requirements.txt

EXPOSE 443

CMD nginx -g 'daemon on;' && python3 /usr/src/certpin/manager.py
