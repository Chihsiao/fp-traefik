import logging
import sys
from typing import Union

from flask import Flask, request
from redis import from_url as redis_from_url

from .config import *
from .frps.conns import *
from .frps.proxies import *
# noinspection PyUnresolvedReferences
from .kv import *
from .utils import *

# region for initialization
logging.basicConfig(format='%(asctime)s [%(levelname)8s] [%(name)s] %(message)s',
                    level=(logging.DEBUG if VERBOSE
                           else logging.INFO))

logger = logging.getLogger('fp_traefik')
redis = redis_from_url(REDIS_URL, **REDIS_KWARGS)

try:
    redis.ping()
    logger.info('connect to redis successfully')
except redis.ConnectionError:
    logger.critical('failed to connect to redis')
    sys.exit(1)
# endregion

app = Flask(__name__)
connection_manager = ConnManager()
proxy_manager = ProxyManager(connection_manager)


@proxy_manager.on_event('register')
@connection_manager.on_event('register')
def _setup_kv(kv_holder: Union[Connection, Proxy]):
    kv_factory, prefixes = KvRegistry[kv_holder.type]
    kv = kv_holder.kv = kv_factory(kv_holder)
    flattened_kv = dict(kv.flattened_items(
        only_extract=prefixes))
    setattr(kv_holder.kv, 'flattened', flattened_kv)
    logger.info('setup kv for %s@%s: %s', kv_holder.name, kv_holder.type, flattened_kv)
    len(flattened_kv) > 0 and redis.mset(flattened_kv)


@proxy_manager.on_event('unregister')
@connection_manager.on_event('unregister')
def _cleanup_kv(kv_holder: Union[Connection, Proxy]):
    if (kv_holder.kv is None) or ((flattened_kv := getattr(kv_holder.kv, 'flattened')) is None): return
    logger.info('cleanup kv for %s@%s', kv_holder.name, kv_holder.type)
    len(flattened_kv) > 0 and redis.delete(*flattened_kv.keys())
    kv_holder.kv = None


@app.post('/handler')
@synchronized()
def frps_handler():
    op = request.args['op']
    content = request.json['content']
    logger.debug('content=%s', content)

    try:
        if op == 'NewWorkConn':
            content_user = content['user']
            connection_manager.register(content_user)

        elif op == 'NewProxy':
            new_proxy_content = content
            proxy_manager.register(new_proxy_content)

        elif op == 'CloseProxy':
            proxy_name = content['proxy_name']
            proxy_manager.unregister(proxy_name)

    except Exception as ex:
        logger.error('failed to handle %s: %s', op, ex)
        return {'reject': True, 'reject_reason': 'internal error in fp-traefik'}

    return {'reject': False, 'unchange': True}


if __name__ == '__main__':
    app.run('0.0.0.0', 8080)
