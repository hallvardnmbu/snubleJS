"""Simple proxy manager for scraping."""

import requests


_URL = ('https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies'
        '&proxy_format=protocolipport&format=text&anonymity=Elite,Anonymous&timeout=20000')


class Proxy:
    """Simple proxy manager for scraping."""
    def __init__(self) -> None:
        """Initialize the `proxies` and `proxy`."""
        self.proxies = []
        self.proxy = self._renew()

    def get(self) -> dict:
        """Returns the current `proxy`."""
        return self.proxy

    def renew(self):
        """
        Updates the `proxy` with the head of `proxies`.
        Updates the `proxies`-list when it's empty.
        """
        if not self.proxies:
            self.proxies = [proxy for proxy in
                            requests.get(_URL).text.split('\r\n')
                            if proxy and proxy.startswith('http')]
        self.proxy = {'http': self.proxies.pop(0)}

    def _renew(self) -> dict:
        """Renew the `proxy` and return it."""
        self.renew()
        return self.proxy
