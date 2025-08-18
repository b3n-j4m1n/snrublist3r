import requests

class HTTPHandler:
    def __init__(self, headers=None, proxies=None, params=None, data=None, timeout=45, session=None):
        self.headers = headers
        self.proxies = proxies
        self.params = params
        self.data = data
        self.timeout = timeout
        self.session = session # currently only used for Google
    
    def get(self, url):
        if self.session:
            response = self.session.get(
                url, 
                headers=self.headers, 
                params=self.params, 
                proxies=self.proxies,
                verify=False, 
                timeout=self.timeout
            )
        else:
            response = requests.get(
                url, 
                headers=self.headers, 
                proxies=self.proxies, 
                params=self.params, 
                verify=False, 
                timeout=self.timeout
            )
        return response
    
    def post(self, url):
        if self.session:
            response = self.session.post(
                url, 
                headers=self.headers, 
                params=self.params, 
                data=self.data, 
                proxies=self.proxies,
                verify=False, 
                timeout=self.timeout
            )
        else:
            response = requests.post(
                url, 
                headers=self.headers, 
                proxies=self.proxies, 
                params=self.params, 
                data=self.data, 
                verify=False, 
                timeout=self.timeout
            )
        return response