FROM nginx
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv git

WORKDIR /usr/src/certpin

COPY manager.py .
COPY requirements.txt .

RUN python3 -m venv /usr/src/certpin/venv
RUN /usr/src/certpin/venv/bin/pip install --no-cache-dir -r requirements.txt

EXPOSE 443

CMD nginx -g 'daemon on;' && /usr/src/certpin/venv/bin/python /usr/src/certpin/manager.py

# Instructions:
#  - docker build -t certpin .
#  - docker run -v ./certpin:/etc/certpin certpin

    