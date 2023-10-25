import logging
import re
import requests

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Back, Style


class RapidDNS:
    def __init__(self, domain_root, proxy, output_file):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.source = "RapidDNS"
        self.results = Results(self.source)

    def run(self):
        logging.warning(f"[*] starting RapidDNS search...")
        url = f"https://rapiddns.io/subdomain/{self.domain_root}?full=1"
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(proxies=proxies)
        eh = ErrorHandler()
        
        try:
            response = hh.get(url)
            response.raise_for_status()
            domains = re.findall(r"(?:[\w-]+[.])+[\w-]+", response.text)
            for domain in domains:
                domain = domain.lower() # preventing different case duplicates
                if (
                    domain.endswith("." + self.domain_root)
                    and domain not in self.results.data[self.source]["subdomains"]
                ):
                    self.results.data[self.source]["subdomains"].add(domain)
                    logging.info(f"{Fore.LIGHTGREEN_EX}[+] {domain}{Style.RESET_ALL}{Fore.WHITE} [RapidDNS]")
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