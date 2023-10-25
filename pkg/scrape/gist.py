import logging
import re
import requests
import time
import sys

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from bs4 import BeautifulSoup
from colorama import Fore, Back, Style


class Gist:
    def __init__(self, domain_root, proxy, output_file):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.source = "Gist"
        self.results = Results(self.source)
        self.gist_links = set()


    def run(self):
        logging.warning("[*] starting Gist query...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        url = "https://gist.github.com/search"
        params = {"q": f'"{self.domain_root}"', "ref": "searchresults"}
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(headers=headers, proxies=proxies, params=params)
        eh = ErrorHandler()
        delay = 5
        i = 1
        
        while i <= 100:
            params["p"] = str(i)
            try:
                response = hh.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "lxml")      
                if "We couldn’t find any gists matching" in soup.text:
                    break
                else:
                    gists = soup.findAll(attrs={"class": "link-overlay"})
                    for gist in gists:
                        href = gist.get('href')
                        self.gist_links.add(href)
                time.sleep(delay)
                i += 1
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    if delay > 30:
                        logging.warning(f"{Fore.LIGHTYELLOW_EX}[!] [Gist] giving up due to excessive HTTP 429 responses (try from a different source IP)")
                        break
                    else:
                        delay += 2
                        logging.warning(f"{Fore.LIGHTYELLOW_EX}[!] [Gist] 429 Too Many Requests, increasing delay and retrying...")
                time.sleep(delay)
            except (
                requests.exceptions.RequestException, 
                NameError,
                ConnectionError,
                TypeError,
                AttributeError,
                KeyboardInterrupt
                ) as e:
                eh.handle_error(e)
                

        for link in self.gist_links:
            url = link
            try:
                response = hh.get(url)
                domains = re.findall(r"(?:[\w-]+[.])+[\w-]+", response.text)
                for domain in domains:
                    if sys.version_info >= (3, 9):
                        domain = domain.lower().removeprefix("x22").removeprefix("2f") # removing leading junk from some results
                    if (
                        domain.endswith("." + self.domain_root)
                        and domain not in self.results.data[self.source]["subdomains"]
                    ):
                        self.results.data[self.source]["subdomains"].add(domain)
                        logging.info(f"{Fore.LIGHTGREEN_EX}[+] {domain}{Style.RESET_ALL}{Fore.WHITE} [Gist]")
            except (
                requests.exceptions.RequestException, 
                NameError,
                ConnectionError,
                TypeError,
                AttributeError,
                KeyboardInterrupt
                ) as e:
                eh.handle_error(e)

        if self.output_file:
            oh = OutputHandler()
            oh.handle_output(self.output_file, self.results.data)

        return self.results.data