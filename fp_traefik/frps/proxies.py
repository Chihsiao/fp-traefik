__all__ = [
    'Proxy',
    'ProxyManager',
]

from typing import Optional, List, Callable

from .conns import Connection, ConnManager


class Proxy:
    def __init__(self, connection: Connection, new_proxy_content: dict):
        self.data, self.kv = new_proxy_content, None
        self.connection = connection

    @property
    def type(self) -> str:
        return self.data['proxy_type']

    @property
    def name(self) -> str:
        return self.data['proxy_name']


class ProxyManager:
    def __init__(self, conn_manager: ConnManager):
        self.conn_manager = conn_manager
        self._listeners = dict()
        self.proxies = dict()

    # region for events
    def listeners(self, event: str, _type: Optional[str]) -> List[Callable]:
        if (by_event := self._listeners.get(event)) is None:
            by_event = self._listeners[event] = dict()
        if (by_type := by_event.get(_type)) is None:
            by_type = by_event[_type] = list()
        return by_type

    def on_event(self,
                 event: str,
                 proxy_type: Optional[str] = None):
        def decorator(listener_func):
            (self.listeners(event, proxy_type)
             .append(listener_func))
            return listener_func

        return decorator
    # endregion

    def register(self, new_proxy_content: dict):
        conn = self.conn_manager.register(new_proxy_content['user'])
        proxy = Proxy(conn, new_proxy_content)
        conn.proxies.add(proxy)
        self.proxies[proxy.name] = proxy
        for a in self.listeners('register', None): a(proxy)
        for a in self.listeners('register', proxy.type): a(proxy)

    def unregister(self, proxy_name: str):
        if (proxy := self.proxies.get(proxy_name)) is None: return
        for a in self.listeners('unregister', proxy.type): a(proxy)
        for a in self.listeners('unregister', None): a(proxy)
        self.proxies.pop(proxy_name, None)
        conn = proxy.connection
        conn.proxies.remove(proxy)
        len(conn.proxies) > 0 or self.conn_manager.unregister(conn.name)
