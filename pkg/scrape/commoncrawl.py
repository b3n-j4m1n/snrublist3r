import logging
import json
import re
import requests

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Back, Style


class CommonCrawl:
    def __init__(self, domain_root, proxy, output_file):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.source = "Common Crawl"
        self.results = Results(self.source)

    def get_indexes(self, response):
        data = json.loads(response.text)
        indexes = [item['id'] for item in data[:10]] # e.g. "id": "CC-MAIN-2024-18", 10 will be about 3 years back
        return indexes

    def run(self):
        logging.info(f"[*] starting CommonCrawl search...")
        headers = headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        index_url = f"https://index.commoncrawl.org/collinfo.json"
        url = f"https://index.commoncrawl.org/"
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(headers=headers, proxies=proxies)
        eh = ErrorHandler()
        
        try:
            index_response = hh.get(index_url)
            indexes = self.get_indexes(index_response)

            for index in indexes:
                url = f"https://index.commoncrawl.org/{index}-index?url=*.{self.domain_root}"
                response = hh.get(url)
                domains = re.findall(r'(?:%252F|//|@)((?:[\w-]+[.])+[\w-]+)', response.text)
                for domain in domains:
                    if (
                        domain.endswith("." + self.domain_root)
                        and domain not in self.results.data[self.source]["subdomains"]
                    ):
                        self.results.data[self.source]["subdomains"].add(domain)
                        logging.info(f"{Fore.LIGHTGREEN_EX}[+] {domain}{Style.RESET_ALL}{Fore.WHITE} [Common Crawl]") 
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