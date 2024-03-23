#!/bin/bash

sudo service nginx stop
docker container stop certpin
docker container rm certpin
docker build . -t certpin
docker run -d --name certpin -p '443:443' -v ./certpin:/etc/certpin certpin
docker exec -it certpin apt install -y curl
echo "To view container logs, use 'docker logs certpin --follow'"
docker exec -it certpin bash
echo "Stopping Container..."
docker container stop certpin

