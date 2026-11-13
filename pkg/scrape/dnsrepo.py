import logging
import re
import requests

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.filter_handler import is_filtered
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Back, Style


class DNSRepo:
    def __init__(self, domain_root, proxy, output_file, filter_strings=None):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.filter_strings = filter_strings
        self.source = "NOC DNS Database Repository Search"
        self.results = Results(self.source)

    def run(self):
        logging.warning(f"[*] starting NOC DNS Database Repository Search search...")
        url = f"https://dnsrepo.noc.org/?domain={self.domain_root}"
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(proxies=proxies)
        eh = ErrorHandler()

        try:
            response = hh.get(url)
            response.raise_for_status()
            domains = re.findall(r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*" + re.escape(self.domain_root), response.text, flags=re.IGNORECASE)
            for domain in domains:
                domain = domain.strip().lower().lstrip("*.").lstrip(".")
                if (
                    domain.endswith("." + self.domain_root)
                    and not is_filtered(domain, self.filter_strings)
                    and domain not in self.results.data[self.source]["subdomains"]
                ):
                    self.results.data[self.source]["subdomains"].add(domain)
                    logging.info(f"{Fore.LIGHTGREEN_EX}[+] {domain}{Style.RESET_ALL}{Fore.WHITE} [NOC DNS Database Repository Search]")
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