import json
import logging
import random
import time
from os import sys

from prometheus_client import Summary, start_http_server
from prometheus_client.registry import REGISTRY

from malina_map_collector import Malina, MapMalinaCollector

_logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)

SOURCES = []
GLOBAL_TIMEOUT = 1
PORT = 26001

CONFIG_FILENAME = sys.argv[1]

with open(CONFIG_FILENAME) as json_file:
    conf = json.load(json_file)
    if 'port' in conf:
        PORT = conf['port']
    if 'timeout' in conf:
        GLOBAL_TIMEOUT = conf['timeout']
    for t in conf['targets']:
        if not 'name' in t or not 'host' in t:
            _logger.error("'name' and 'host' are required")
        timeout = GLOBAL_TIMEOUT
        if 'timeout' in t:
            timeout = t['timeout']    
        SOURCES.append(Malina(t['name'],t['host'],t['login'],t['password'],timeout=timeout))
                

if __name__ == '__main__':
    try:        
        REGISTRY.register(MapMalinaCollector(SOURCES))
        start_http_server(PORT)
        #
        while True:
            time.sleep(1)
            # process_request(random.random())
    except KeyboardInterrupt:
        _logger.info("Interrupted. Exiting")
        exit(0)
