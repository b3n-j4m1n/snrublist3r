import logging
import json
import requests

from urllib.parse import urlparse

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Style


class HudsonRock:
    def __init__(self, domain_root, proxy, output_file):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.source = "Hudson Rock"
        self.results = Results(self.source)

    def run(self):
        logging.warning(f"[*] starting Hudson Rock query...")
        url = f"https://cavalier.hudsonrock.com/api/json/v2/osint-tools/urls-by-domain?domain={self.domain_root}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(headers=headers, proxies=proxies)
        eh = ErrorHandler()

        try:
            response = hh.get(url)
            response.raise_for_status()
            data = response.json()
            urls = data.get("data", {}).get("employees_urls", []) + data.get("data", {}).get("clients_urls", [])
            for entry in urls:
                hostname = urlparse(entry["url"]).hostname
                if not hostname or '*' in hostname: # removing censored domains
                    continue
                if hostname.endswith("." + self.domain_root) and hostname not in self.results.data[self.source]["subdomains"]:
                    self.results.data[self.source]["subdomains"].add(hostname)
                    logging.info(f"{Fore.LIGHTGREEN_EX}[+] {hostname}{Style.RESET_ALL}{Fore.WHITE} [Hudson Rock]")
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
