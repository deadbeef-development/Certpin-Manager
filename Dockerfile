#FROM nginx
FROM ubuntu:focal

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y python3 python3-pip python3-venv git nginx

WORKDIR /usr/src/certpin

COPY manager.py .
COPY requirements.txt .

RUN python3 -m venv /usr/src/certpin/venv
RUN /usr/src/certpin/venv/bin/pip install --no-cache-dir -r requirements.txt

EXPOSE 443

CMD /usr/src/certpin/venv/bin/python -u /usr/src/certpin/manager.py

# Instructions:
#  - docker build . -t certpin
#  - docker run certpin --name certpin -p 443:443 -v ./certpin:/etc/certpin

    