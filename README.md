# Certpin-Manager
## Instructions:
```bash
docker build . -t certpin
docker run certpin --name certpin -p 443:443 -v ./certpin:/etc/certpin
```

