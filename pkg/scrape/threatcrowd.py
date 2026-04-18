import logging
import json
import requests

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Style


class ThreatCrowd:
    def __init__(self, domain_root, proxy, output_file):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.source = "ThreatCrowd"
        self.results = Results(self.source)

    def run(self):
        logging.warning(f"[*] starting ThreatCrowd query...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
        }
        url = f"http://ci-www.threatcrowd.org/searchApi/v2/domain/report/?domain={self.domain_root}"
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(headers=headers, proxies=proxies)
        eh = ErrorHandler()

        try:
            response = hh.get(url)
            if "failedConnection" in response.text:
                logging.debug(f"{Fore.LIGHTYELLOW_EX}[!] [ThreatCrowd] 200 Connection failed: Too many connections")
                return self.results.data
            response.raise_for_status()
            data = response.json()
            if "subdomains" in data:
                for subdomain in data["subdomains"]:
                    if subdomain.endswith("." + self.domain_root):
                        self.results.data[self.source]["subdomains"].add(subdomain)
                for subdomain in self.results.data[self.source]["subdomains"]:
                    logging.info(f"{Fore.LIGHTGREEN_EX}[+] {subdomain}{Style.RESET_ALL}{Fore.WHITE} [ThreatCrowd]") 
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
