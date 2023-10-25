import logging
import requests
import json

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Back, Style

class CertificateSearch:
    def __init__(self, domain_root, proxy, output_file):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.source = "Certificate Search"
        self.results = Results(self.source)


    def run(self):
        logging.info("[*] starting certificate transparency search...")
        url = "https://crt.sh"
        params = {
            "q": f"{self.domain_root}",
            "output": "json"
        }
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(proxies=proxies, params=params, timeout=120)
        eh = ErrorHandler()

        try:
            response = hh.get(url)
            response.raise_for_status()
            data = response.json()
            for item in data:
                domains = item['name_value'].split('\n')
                for domain in domains:
                    if domain.startswith("*"):
                        domain = domain[2:] # remove the "*."
                    if domain.endswith("." + self.domain_root) and "@" not in domain: # filtering out email addresses
                        self.results.data[self.source]["subdomains"].add(domain)
            for subdomain in self.results.data[self.source]["subdomains"]:
                logging.info(f"{Fore.LIGHTGREEN_EX}[+] {subdomain}{Style.RESET_ALL}{Fore.WHITE} [Certifcate Search]")
        except (
            requests.exceptions.RequestException, 
            NameError, 
            json.decoder.JSONDecodeError,
            ConnectionError,
            TypeError, 
            AttributeError, 
            KeyboardInterrupt
            ) as e:
            eh.handle_error(e, self.source)
        
        if self.output_file:
            oh = OutputHandler()
            oh.handle_output(self.output_file, self.results.data)

        return self.results.data