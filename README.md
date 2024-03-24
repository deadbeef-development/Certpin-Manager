# Certpin-Manager
## Instructions:

To get started, create a folder called `certpin`.

The `certpin` folder will be mounted in the container.
Aside from the `config.json`, it will also require that you put three different files in it:
1. The Pinned Certificate in DER form. Put it in `./certpin/pinned_certs`. You can "grab" the current certificate of a server using `python3 -m certpin.capture`. Be careful though, as this utility does NOT verify the certificate. The reason is because the premise of certificate pinning ensures security precision *for insecure servers*, but does not guarantee accuracy at the time of capture.
2. The Site Certificate in PEM form. Put it in `./certpin/site_certs`. This will be used by Nginx in the container.
3. The Site Key in PEM form. Put it in `./certpin/site_keys`. This will be used by Nginx in the container

Then, use the example configuration below to draft a `config.json` file in the `certpin` folder mentioned above.
For each site, the `pinned_cert`, `site_cert`, and `site_key` items require the name of certificate/key file relative to the `./certpin/pinned_certs`, `./certpin/site_certs`, and `./certpin/site_keys` directories respectively.

For each site item:
- `server_name`: The FQDN of the server.
- `upstream_host`: The server to proxy to, whose cert is pinned.
- `upstream_port`: The server port.
- `upstream_server_name`: Optional, use this for SNI.
- `pinned_cert`: The pinned certificate of the server to proxy to.
- `site_cert`: The certificate of the server.
- `site_key`: The private key of the server.
- `host_header`: Optional, sets the Host header when clients are proxied.

**File: `config.json`**
```json
{
    "sites": [
        {
            "server_name": "example.com.certpin.dbdev.me",
            "upstream_host": "example.com",
            "upstream_port": 443,
            "upstream_server_name": "example.com",
            "pinned_cert": "example.com.cert.der",
            "site_cert": "example.com.certpin.dbdev.me.cert.pem",
            "site_key": "example.com.certpin.dbdev.me.privkey.pem",
            "host_header": "example.com"
        }
    ]
}
```

Once everything is configured, you can build the image and run the container:
```bash
docker build . -t certpin
docker run -d --name certpin -p '443:443' -v ./certpin:/etc/certpin certpin
```

