import requests

class HTTPHandler:
    def __init__(self, headers=None, proxies=None, params=None, data=None, timeout=30):
        self.headers = headers
        self.proxies = proxies
        self.params = params
        self.data = data
        self.timeout = timeout

    def get(self, url):
        response = requests.get(url, headers=self.headers, proxies=self.proxies, params=self.params, verify=False, timeout=self.timeout)
        return response

    def post(self, url):
        response = requests.post(url, headers=self.headers, proxies=self.proxies, params=self.params, data=self.data, verify=False, timeout=self.timeout)
        return response