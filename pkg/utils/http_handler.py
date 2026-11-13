import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class HTTPHandler:
    def __init__(self, headers=None, proxies=None, params=None, data=None, timeout=45, session=None):
        self.headers = headers
        self.proxies = proxies
        self.params = params
        self.data = data
        self.timeout = timeout
        if session is not None:
            self.session = session
        else:
            retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
            adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=retry)
            self.session = requests.Session()
            self.session.mount('https://', adapter)
            self.session.mount('http://', adapter)

    def get(self, url):
        response = self.session.get(
            url,
            headers=self.headers,
            params=self.params,
            proxies=self.proxies,
            verify=False,
            timeout=self.timeout
        )
        return response

    def post(self, url):
        response = self.session.post(
            url,
            headers=self.headers,
            params=self.params,
            data=self.data,
            proxies=self.proxies,
            verify=False,
            timeout=self.timeout
        )
        return response