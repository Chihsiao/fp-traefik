__all__ = [
    'Connection',
    'ConnManager',
]

from typing import Callable, List


class Connection:
    def __init__(self, content_user: dict):
        self.data, self.kv = content_user, None
        self.proxies = set()

    @property
    def type(self) -> str:
        return 'conn'

    @property
    def name(self) -> str:
        return self.data['run_id']


class ConnManager:
    def __init__(self):
        self._listeners = dict()
        self.connections = dict()

    # region for events
    def listeners(self, event: str) -> List[Callable]:
        if (ret := self._listeners.get(event)) is None:
            ret = self._listeners[event] = list()
        return ret

    def on_event(self, event: str):
        def decorator(listener_func: Callable[[Connection], None]):
            self.listeners(event).append(listener_func)
            return listener_func

        return decorator
    # endregion

    def register(self, content_user: dict) -> Connection:
        run_id = content_user['run_id']
        if (conn := self.connections.get(run_id)) is None:
            conn = self.connections[run_id] = Connection(content_user)
            for a in self.listeners('register'): a(conn)
        return conn

    def unregister(self, run_id: str):
        if (conn := self.connections.get(run_id)) is None: return
        assert len(conn.proxies) == 0, f'connection {run_id} should have no proxies'
        for a in self.listeners('unregister'): a(conn)
        self.connections.pop(run_id, None)
