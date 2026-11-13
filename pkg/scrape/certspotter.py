import logging
import json
import requests

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.filter_handler import is_filtered
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Style


class CertSpotter:
    def __init__(self, domain_root, proxy, output_file, filter_strings=None):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.filter_strings = filter_strings
        self.source = "Cert Spotter"
        self.results = Results(self.source)

    def run(self):
        logging.warning(f"[*] starting Cert Spotter query...")
        url = f"https://api.certspotter.com/v1/issuances?domain={self.domain_root}&include_subdomains=true&expand=dns_names"
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(proxies=proxies)
        eh = ErrorHandler()

        try:
            response = hh.get(url)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list):
                raise TypeError("unexpected Cert Spotter response format")
            for entry in data:
                for name in entry.get("dns_names", []):
                    name = name.strip().lower().lstrip("*.").lstrip(".")
                    if (
                        name.endswith("." + self.domain_root)
                        and not is_filtered(name, self.filter_strings)
                        and name not in self.results.data[self.source]["subdomains"]
                    ):
                        self.results.data[self.source]["subdomains"].add(name)
                        logging.info(f"{Fore.LIGHTGREEN_EX}[+] {name}{Style.RESET_ALL}{Fore.WHITE} [Cert Spotter]")
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