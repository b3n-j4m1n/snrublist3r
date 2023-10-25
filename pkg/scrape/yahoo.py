import logging
import requests

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from bs4 import BeautifulSoup
from colorama import Fore, Back, Style


class Yahoo:
    def __init__(self, domain_root, proxy, output_file):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.source = "Yahoo"
        self.results = Results(self.source)


    def run(self):
        logging.info(f"[*] starting Yahoo search...")
        headers = headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        url = "https://search.yahoo.com/search"
        params = {
            "p": "site:" + self.domain_root,
            "xargs": 0
        }
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(headers=headers, proxies=proxies, params=params)
        eh = ErrorHandler()
        
        try:
            for i in range(1, 101, 9):
                params["b"] = str(i)
                response = hh.get(url)
                soup = BeautifulSoup(response.text, "lxml")
                if "We did not find results for" in soup.text:
                    break
                links = soup.find_all(attrs={"class": "d-ib p-abs t-0 l-0 fz-14 lh-20 fc-obsidian wr-bw ls-n pb-4"})
                for link in links:
                    domain = link.text.split(" ")[0]
                    if (
                        domain.endswith("." + self.domain_root)
                        and domain not in self.results.data[self.source]["subdomains"]
                    ):
                        self.results.data[self.source]["subdomains"].add(domain)
                        logging.info(f"{Fore.LIGHTGREEN_EX}[+] {domain}{Style.RESET_ALL}{Fore.WHITE} [Yahoo]") 
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