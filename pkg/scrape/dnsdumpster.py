import logging
import re
import requests
import sys

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from bs4 import BeautifulSoup
from colorama import Fore, Back, Style


class DNSDumpster:
    def __init__(self, domain_root, proxy, output_file):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.source = "DNSDumpster"
        self.results = Results(self.source)


    def get_authorization_token(self, response):
        authorization_key_pair = re.search(r'"Authorization":\s*"([^"]*)"', response.text)
        authorization_token = authorization_key_pair.group(1)
        return authorization_token
    
    def run(self):
        logging.info("[*] starting DNSDumpster query...")
        authorization_url = f"https://dnsdumpster.com/"
        url = f"https://api.dnsdumpster.com/htmld/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(headers=headers, proxies=proxies)
        eh = ErrorHandler()
        try:
            authorization_response = hh.get(authorization_url)
            authorization_token = self.get_authorization_token(authorization_response)
            headers.update(
                {"Authorization": authorization_token}
            )
        except:
            logging.error(Fore.LIGHTRED_EX + "[-] [DNSDumpster] error getting Authorization token")
            return self.results.data
        
        data = {"target": self.domain_root}
        hh = HTTPHandler(headers=headers, proxies=proxies, data=data)
        try:
            response = hh.post(url)
            response.raise_for_status()
            domains = re.findall(r"\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", response.text)
            soup = BeautifulSoup(response.text, "lxml")
            links = soup.findAll("td")
            for domain in domains:
                if sys.version_info >= (3, 9):
                    domain = domain.lower().removeprefix(".") # preventing different case duplicates and removing leading junk from some results
                if (
                    domain.endswith("." + self.domain_root)
                    and domain not in self.results.data[self.source]["subdomains"]
                ):
                    self.results.data[self.source]["subdomains"].add(domain)
                    logging.info(f"{Fore.LIGHTGREEN_EX}[+] {domain}{Style.RESET_ALL}{Fore.WHITE} [DNSDumpster]")
        except (
            requests.exceptions.RequestException, 
            NameError,
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