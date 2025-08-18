import logging
import json
import requests
import base64
import sys

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Style


class Chaos:
    def __init__(self, domain_root, proxy, output_file):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.source = "Chaos"
        self.results = Results(self.source)

    def run(self):
        logging.warning(f"[*] starting Chaos query...")
        key = "ODg2YmFjMWQtMjgxOC00YWQ1LWE5ZDgtN2QyMjA0OTFmOWNl"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
            "Authorization": base64.b64decode(key).decode('utf-8')
        }
        url = f"https://dns.projectdiscovery.io/dns/{self.domain_root}/subdomains"
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(headers=headers, proxies=proxies)
        eh = ErrorHandler()

        try:
            response = hh.get(url)
            response.raise_for_status()
            data = response.json()
            for subdomain in data["subdomains"]:
                if subdomain == "*":
                    continue
                if subdomain.startswith("*."):
                    subdomain = subdomain[2:]
                if subdomain.startswith("_dmarc"):  # removing DMARC records
                    continue
                if not subdomain: # removing empty "" subdomains
                    continue
                domain = f"{subdomain}.{self.domain_root}"
                self.results.data[self.source]["subdomains"].add(domain)
            for subdomain in self.results.data[self.source]["subdomains"]:
                logging.info(f"{Fore.LIGHTGREEN_EX}[+] {subdomain}{Style.RESET_ALL}{Fore.WHITE} [Chaos]")
                    
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
