from logging import getLogger

from ..config import *
from ..frps.conns import Connection
from ..utils import LeveledKv

logger = getLogger(__name__)


class ConnKv(LeveledKv):
    def __init__(self, conn: Connection):
        super().__init__(conn.data.get('metas'))
        self.conn = conn


KvRegistry['conn'] = (ConnKv, (f'{ROOT_KEY}/',))
