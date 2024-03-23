from typing import List
import os
import sys
import json
from threading import Thread, Event
from functools import partial
from contextlib import contextmanager
from subprocess import Popen, TimeoutExpired
import atexit
from socketserver import ThreadingTCPServer

from certpin.server import run_certpin_server

NGINX_SITES_DIR = "/etc/nginx/conf.d"
CERTPIN_DIR_PATH = "/etc/certpin"
PINNED_CERTS_DIR_PATH = CERTPIN_DIR_PATH + "/pinned_certs"
SITE_CERTS_DIR_PATH = CERTPIN_DIR_PATH + "/site_certs"
SITE_KEYS_DIR_PATH = CERTPIN_DIR_PATH + "/site_keys"
CONFIG_FILE_PATH = CERTPIN_DIR_PATH + "/config.json"
CERTPIN_BIND_ADDR = ('127.0.0.1', 0)

NGINX_CONFIG_TEMPLATE = \
"""
server {{
    listen 443 ssl;
    server_name {server_name};

    ssl_certificate {site_cert};
    ssl_certificate_key {site_privkey};

    location / {{
        proxy_pass http://127.0.0.1:{certpin_port};
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-Port 443;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}
}}
"""

def kill_subprocess(proc):
    try:
        proc.terminate()
        proc.wait(timeout=10)
    except TimeoutExpired:
        proc.kill()

def run_nginx() -> Popen:
    cmd = ["nginx", "-g", "daemon off;"]

    proc = Popen(cmd, start_new_session=True)

    atexit.register(kill_subprocess, proc)

    return proc

@contextmanager
def run_site(
    server_name: str, 
    upstream_server_name: str, upstream_host: str, upstream_port: int,
    pinned_cert_file_path: str,
    site_cert_file_path: str, site_key_file_path: str
):
    nginx_config_file_path = NGINX_SITES_DIR + '/' + upstream_server_name + '.conf'

    ssl_target_addr = (upstream_host, upstream_port)

    context = run_certpin_server(CERTPIN_BIND_ADDR, 
        ssl_target_addr=ssl_target_addr,
        target_server_name=upstream_server_name,
        pinned_cert_filepath=pinned_cert_file_path
    )

    with context as server:
        certpin_host, certpin_port = server.server_address

        nginx_config = NGINX_CONFIG_TEMPLATE.format(
            server_name=server_name,
            site_cert=site_cert_file_path,
            site_privkey=site_key_file_path,
            certpin_port=certpin_port
        )

        with open(nginx_config_file_path, 'w') as fio:
            fio.write(nginx_config)

        yield server

def run_site_from_config(
        pinned_cert: str = None, 
        site_cert: str = None, 
        site_key: str = None,
        **kwargs
) -> Thread:
    pinned_cert_file_path = PINNED_CERTS_DIR_PATH + '/' + pinned_cert
    site_cert_file_path = SITE_CERTS_DIR_PATH + '/' + site_cert
    site_key_file_path = SITE_KEYS_DIR_PATH + '/' + site_key

    context = run_site(
        pinned_cert_file_path=pinned_cert_file_path,
        site_cert_file_path=site_cert_file_path,
        site_key_file_path=site_key_file_path,
        **kwargs
    )

    def target():
        with context as server:
            server.serve_forever()

    t = Thread(None, target)
    t.start()

    return t

def __main__(args: List[str]):
    os.makedirs(PINNED_CERTS_DIR_PATH, exist_ok=True)
    os.makedirs(SITE_CERTS_DIR_PATH, exist_ok=True)
    os.makedirs(SITE_KEYS_DIR_PATH, exist_ok=True)

    with open(CONFIG_FILE_PATH, 'r') as fio:
        config = json.load(fio)
    
    threads: List[Thread] = list()

    for site_config in config['sites']:
        t = run_site_from_config(**site_config)
        threads.append(t)
    
    run_nginx()
    
    for t in threads:
        t.join()

if __name__ == '__main__':
    __main__(sys.argv)

