import logging
import json
import requests

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Style


class THC:
    def __init__(self, domain_root, proxy, output_file):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.source = "THC"
        self.results = Results(self.source)

    def run(self):
        logging.warning(f"[*] starting THC query...")
        url = "https://ip.thc.org/api/v1/lookup/subdomains"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0",
        }
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        eh = ErrorHandler()

        try:
            page_state = ""
            while True:
                body = json.dumps({"domain": self.domain_root, "page_state": page_state, "limit": 1000})
                hh = HTTPHandler(headers=headers, proxies=proxies, data=body)
                response = hh.post(url)
                response.raise_for_status()
                data = response.json()
                for record in data.get("domains", []):
                    domain = record.get("domain", "")
                    if domain.endswith("." + self.domain_root) and domain not in self.results.data[self.source]["subdomains"]:
                        self.results.data[self.source]["subdomains"].add(domain)
                        logging.info(f"{Fore.LIGHTGREEN_EX}[+] {domain}{Style.RESET_ALL}{Fore.WHITE} [THC]")
                page_state = data.get("next_page_state", "")
                if not page_state:
                    break
        except (
            requests.exceptions.RequestException,
            NameError,
            json.decoder.JSONDecodeError,
            ConnectionError,
            TypeError,
            AttributeError,
            KeyboardInterrupt,
            ) as e:
            eh.handle_error(e, self.source)

        if self.output_file:
            oh = OutputHandler()
            oh.handle_output(self.output_file, self.results.data)

        return self.results.data
