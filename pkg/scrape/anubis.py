import logging
import json
import requests
import sys

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from bs4 import BeautifulSoup
from colorama import Fore, Back, Style


class Anubis:
    def __init__(self, domain_root, proxy, output_file):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.source = "Anubis"
        self.results = Results(self.source)


    def run(self):
        logging.warning(f"[*] starting Anubis search...")
        url = f"https://jonlu.ca/anubis/subdomains/{self.domain_root}"
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(proxies=proxies)
        eh = ErrorHandler()
        
        try:
            response = hh.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            anubis_json = json.loads(soup.text)
            for domain in anubis_json:
                if sys.version_info >= (3, 9):
                    domain = domain.lower().removeprefix("x22").removeprefix("2f").removeprefix("u002f") # removing leading junk from some results
                self.results.data[self.source]["subdomains"].add(domain)
                logging.info(f"{Fore.LIGHTGREEN_EX}[+] {domain}{Style.RESET_ALL}{Fore.WHITE} [Anubis]")
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
