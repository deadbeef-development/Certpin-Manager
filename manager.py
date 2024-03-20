from typing import List
import os
import sys
import json
from threading import Thread, Event
from functools import partial
from contextlib import contextmanager

from certpin.server import run_certpin_server

NGINX_SITES_DIR = "/etc/nginx/sites-enabled"
CERTPIN_DIR_PATH = "/etc/certpin"
PINNED_CERTS_DIR_PATH = CERTPIN_DIR_PATH + "/pinned_certs"
CONFIG_FILE_PATH = CERTPIN_DIR_PATH + "/config.json"
CERT_FILE_PATH = CERTPIN_DIR_PATH + "/site_cert.pem"
PRIVKEY_FILE_PATH = CERTPIN_DIR_PATH + "/site_privkey.pem"
CERTPIN_BIND_ADDR = ('127.0.0.1', 0)

NGINX_CONFIG_TEMPLATE = \
"""
server {
    listen 443 ssl;
    server_name {server_name};

    ssl_certificate {site_cert};
    ssl_certificate_key {site_privkey};

    location / {
        proxy_pass http://127.0.0.1:{certpin_port};
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-Port 443;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
"""

reload_nginx = partial(os.system, "sudo nginx -s reload")

@contextmanager
def run_site(server_name: str, upstream_server_name: str, upstream_host: str, upstream_port: int):
    pinned_cert_filepath = PINNED_CERTS_DIR_PATH + '/' + upstream_server_name + '.pem'
    nginx_config_file_path = NGINX_SITES_DIR + '/' + upstream_server_name + '.conf'

    ssl_target_addr = (upstream_host, upstream_port)

    context = run_certpin_server(CERTPIN_BIND_ADDR, 
        ssl_target_addr=ssl_target_addr,
        target_server_name=upstream_server_name,
        pinned_cert_filepath=pinned_cert_filepath
    )

    with context as server:
        certpin_host, certpin_port = server.server_address

        nginx_config = NGINX_CONFIG_TEMPLATE.format(
            server_name=server_name,
            site_cert=CERT_FILE_PATH,
            site_privkey=PRIVKEY_FILE_PATH,
            certpin_port=certpin_port
        )

        with open(nginx_config_file_path, 'w') as fio:
            fio.write(nginx_config)

        yield server

def run_site_from_config(site_config: dict, ready: Event) -> Thread:
    def target():
        try:
            with run_site(**site_config) as server:
                ready.set()
                server.serve_forever()
        finally:
            ready.set()
    
    t = Thread(None, target)
    t.start()

    return t

def __main__(args: List[str]):
    os.makedirs(PINNED_CERTS_DIR_PATH)

    with open(CONFIG_FILE_PATH, 'r') as fio:
        config = json.load(fio)
    
    threads: List[Thread] = list()
    ready_events: List[Event] = list()

    for site_config in config['sites']:
        ready = Event()
        t = run_site_from_config(site_config, ready)

        ready_events.append(ready)
        threads.append(t)
    
    for ready in ready_events:
        ready.wait()
    
    reload_nginx()
    
    for t in threads:
        t.join()

if __name__ == '__main__':
    __main__(sys.argv)

