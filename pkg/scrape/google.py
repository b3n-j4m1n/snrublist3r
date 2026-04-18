import logging
import re
import random
import requests
import sys
import time

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Back, Style


class Google:
    def __init__(self, domain_root, proxy, output_file):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.source = "Google"
        self.session = requests.Session() # needed for NID cookie
        if self.proxy:
            self.session.proxies.update({"http": self.proxy, "https": self.proxy})
        self.results = Results(self.source)

    def normal_query(self):
        url = "https://www.google.com.au/search"
        normal_queries = ["homer", "marge", "bart", "lisa", "maggie"]
        normal_params = {"q": random.choice(normal_queries)}
        headers = {
                    "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7", # very old Firefox version from 2009, modern user agents will trigger a JavaScript check and redirect to "enable JavaScript" page
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Dnt": "1",
                    "Sec-Gpc": "1",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "same-origin",
                    "Priority": "u=0, i",
                    "Te": "trailers"
        }
        eh = ErrorHandler()
        hh = HTTPHandler(headers=headers, params=normal_params, session=self.session)
        try:
            hh.get(url)
        except (
            requests.exceptions.RequestException,
            NameError,
            ConnectionError,
            TypeError,
            AttributeError,
            KeyboardInterrupt
            ) as e:
            eh.handle_error(e, self.source)
        time.sleep(10)

    def run(self):
        logging.warning("[*] starting Google query...")
        url = "https://www.google.com.au/search"
        params = {
            "q": f"site:{self.domain_root}",
            "filter": "0",
            "num": "100"
        }
        eh = ErrorHandler()

        try:

            # initial request to get the cookies
            headers = {
                        "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7", # very old Firefox version from 2009, modern user agents will trigger a JavaScript check and redirect to "enable JavaScript" page
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Dnt": "1",
                        "Sec-Gpc": "1",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "same-origin",
                        "Priority": "u=0, i",
                        "Te": "trailers"
                    }
            params["start"] = "0"

            hh = HTTPHandler(headers=headers, params=params, session=self.session)
            response = hh.get(url)

            response.raise_for_status()

            for i in range(0, 1001, 100):
                params["start"] = str(i)
                hh = HTTPHandler(headers=headers, params=params, session=self.session)
                response = hh.get(url)
                response.raise_for_status()

                if "did not match any documents" in response.text:
                    break
                domains = re.findall(r"(?<!2f)(?:[\w-]+[.])+[\w-]+", response.text, flags=re.IGNORECASE)
                for domain in domains:
                    if sys.version_info >= (3, 9):
                        domain = domain.lower().removeprefix("x22").removeprefix("2f")  # removing leading junk from some results
                    if (
                        domain.endswith("." + self.domain_root)
                        and domain not in self.results.data[self.source]["subdomains"]
                    ):
                        self.results.data[self.source]["subdomains"].add(domain)
                        logging.info(f"{Fore.LIGHTGREEN_EX}[+] {domain}{Style.RESET_ALL}{Fore.WHITE} [Google]")
                self.normal_query()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logging.debug(f"{Fore.LIGHTYELLOW_EX}[!] [Google] 429 Too Many Requests")
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