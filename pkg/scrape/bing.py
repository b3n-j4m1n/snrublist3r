import logging
import re
import requests
import sys

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Back, Style


class Bing:
    def __init__(self, domain_root, proxy, output_file):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.source = "Bing"
        self.results = Results(self.source)
        

    def run(self):
        logging.info("[*] starting Bing query...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        url = f"https://www.bing.com/search"
        params = {
            "q": f"site:{self.domain_root}", # this sets the search query to search for pages on the {self.domain_root} website
            "qn": "n", # this sets the query source to "unknown"
            "sp": "-1", #this sets the query spelling correction to off
            "sc": "1-100", # this sets the "search history" parameter to show results from the past 1-100 days
            "sk": "" # this sets the "skip" parameter to 0, indicating that no results should be skipped
        }
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(headers=headers, proxies=proxies, params=params)
        eh = ErrorHandler()


        try:
            for i in range(1, 200, 10):
                params["first"] = str(i)
                response = hh.get(url)
                response.raise_for_status()
                if "There are no results for " in response.text:
                    break
                else:
                    domains = re.findall(r"(?<!2f)(?:[\w-]+[.])+[\w-]+", response.text)
                    for domain in domains:
                        if sys.version_info >= (3, 9):
                            domain = domain.lower().removeprefix("x22").removeprefix("2f") # removing leading junk from some results
                        if (
                            domain.endswith("." + self.domain_root)
                            and domain not in self.results.data[self.source]["subdomains"]
                        ):
                            self.results.data[self.source]["subdomains"].add(domain)
                            logging.info(f"{Fore.LIGHTGREEN_EX}[+] {domain}{Style.RESET_ALL}{Fore.WHITE} [Bing]")
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