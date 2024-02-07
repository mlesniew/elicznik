from urllib3 import poolmanager
import ssl

import requests


LOGIN_URL = "https://logowanie.tauron-dystrybucja.pl/login"
BLOCK_URL = "https://elicznik.tauron-dystrybucja.pl/blokada"

def _handle_ban_and_auth(r:requests.Request, *args, **kwargs):
    if r.url == BLOCK_URL:
        raise RuntimeError("you have been banned")

    if r.url == LOGIN_URL and 'Login lub has' in r.text:
        raise RuntimeError("invalid login or password")


# Workaround for https://github.com/psf/requests/issues/4775
class TLSAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        """Create and initialize the urllib3 PoolManager."""
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        self.poolmanager = poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_version=ssl.PROTOCOL_TLS,
            ssl_context=ctx,
        )


class Session(requests.Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hooks={ "response": [_handle_ban_and_auth] }
        self.mount("https://", TLSAdapter())
