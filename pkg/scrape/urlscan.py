import logging
import requests
import json

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.filter_handler import is_filtered
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Back, Style


class URLScan:
    MAX_PAGES = 10
    PAGE_SIZE = 10000

    def __init__(self, domain_root, proxy, output_file, filter_strings=None):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.filter_strings = filter_strings
        self.source = "URLScan"
        self.results = Results(self.source)


    def run(self):
        logging.warning(f"[*] starting urlscan search...")
        url = "https://urlscan.io/api/v1/search/"
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(proxies=proxies, timeout=60)
        eh = ErrorHandler()

        try:
            search_after = None
            for page in range(self.MAX_PAGES):
                params = {
                    "q": f"domain:{self.domain_root}",
                    "size": self.PAGE_SIZE
                }
                if search_after is not None:
                    params["search_after"] = ",".join(str(item) for item in search_after)
                hh.params = params
                response = hh.get(url)
                response.raise_for_status()
                data = response.json()
                for item in data.get("results", []):
                    domain = (item.get("page") or {}).get("domain")
                    if not domain:
                        continue
                    if domain.startswith("*."):
                        domain = domain[2:] # remove the "*."
                    if (
                        domain.endswith("." + self.domain_root)
                        and not is_filtered(domain, self.filter_strings)
                        and domain not in self.results.data[self.source]["subdomains"]
                    ):
                        self.results.data[self.source]["subdomains"].add(domain)
                        logging.info(f"{Fore.LIGHTGREEN_EX}[+] {domain}{Style.RESET_ALL}{Fore.WHITE} [URLScan]")
                if not data.get("has_more") or not data.get("search_after"):
                    break
                search_after = data["search_after"]
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logging.debug(f"{Fore.LIGHTYELLOW_EX}[!] [Urlscan] 429 Too Many Requests")
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