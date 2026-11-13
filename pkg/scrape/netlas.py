import logging
import json
import requests

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.filter_handler import is_filtered
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Style


class Netlas:
    def __init__(self, domain_root, proxy, output_file, filter_strings=None):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.filter_strings = filter_strings
        self.source = "Netlas"
        self.results = Results(self.source)

    def run(self):
        logging.warning(f"[*] starting Netlas query...")
        url = "https://app.netlas.io/api/domains/"
        params = {"q": f"domain:*.{self.domain_root}", "source_type": "include", "start": 0, "count": 200}
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(proxies=proxies, params=params, timeout=30)
        eh = ErrorHandler()

        try:
            response = hh.get(url)
            response.raise_for_status()
            data = response.json()
            for item in data.get("items", []) or []:
                domain_data = item.get("data", {}) or {}
                for field in ("host", "domain"):
                    host = str(domain_data.get(field, "")).strip().lower().lstrip("*.").lstrip(".")
                    if (
                        host.endswith("." + self.domain_root)
                        and not is_filtered(host, self.filter_strings)
                        and host not in self.results.data[self.source]["subdomains"]
                    ):
                        self.results.data[self.source]["subdomains"].add(host)
                        logging.info(f"{Fore.LIGHTGREEN_EX}[+] {host}{Style.RESET_ALL}{Fore.WHITE} [Netlas]")
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