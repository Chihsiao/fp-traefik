from logging import getLogger

from ..config import *
from ..frps.proxies import Proxy
from ..rules import host, path_prefix, match_any, match_all
from ..utils import LeveledKv, lazy

logger = getLogger(__name__)


class HttpKv(LeveledKv):
    def __init__(self, proxy: Proxy):
        super().__init__(proxy.data.get('metas'))
        self.proxy = proxy
        self.configure()

    def configure(self):
        @lazy
        def build_rule():
            rules = []

            def build_hosts():
                _hosts = []

                if custom_domains := self.proxy.data.get('custom_domains'):
                    _hosts.extend(custom_domains)

                if subdomain := self.proxy.data.get('subdomain'):
                    if SUBDOMAIN_HOST: _hosts.append(f'{subdomain}.{SUBDOMAIN_HOST}')
                    else: logger.warning('failed to configure subdomain for %s@%s, lacking SUBDOMAIN_HOST',
                                         self.proxy.name, self.proxy.type)

                return _hosts

            if hosts := build_hosts(): rules.append(match_any(host(h) for h in hosts))
            else: logger.warning('no hosts for %s@%s', self.proxy.name, self.proxy.type)

            if path_prefixes := self.proxy.data.get('locations'):
                rules.append(match_any(path_prefix(p) for p in path_prefixes))

            return match_all(rules)

        routers_kv = self['traefik/http/routers/']

        if len(routers_kv.keys()) == 0:
            if DEFAULT_ROUTER_NAME_PREFIX: routers_kv.next_level(DEFAULT_ROUTER_NAME_PREFIX + self.proxy.name)
            else: logger.warning('failed to set default router for %s@%s, lacking DEFAULT_ROUTER_NAME_PREFIX',
                                 self.proxy.name, self.proxy.type)

        for router, router_kv in routers_kv.items():
            if not router.endswith('/'): continue
            router = router[:-1]  # strip slash

            if not router_kv['rule']:
                if rule := build_rule(): router_kv['rule'] = rule
                else: logger.warning('no rule for router %s', router)

            if not router_kv['service']:
                if DEFAULT_SERVICE: router_kv['service'] = DEFAULT_SERVICE
                else: logger.warning('failed to set default service for router %s, '
                                     'lacking DEFAULT_SERVICE', router)

            if len(router_kv['entryPoints/'].keys()) == 0:
                if DEFAULT_ENTRYPOINT: router_kv['entryPoints/0'] = DEFAULT_ENTRYPOINT
                else: logger.warning('failed to set default entry point for router %s, '
                                     'lacking DEFAULT_ENTRYPOINT', router)


KvRegistry['http'] = (HttpKv, ('traefik/',))
