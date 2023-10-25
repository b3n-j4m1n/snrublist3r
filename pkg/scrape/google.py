import logging
import random
import requests
import time

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from bs4 import BeautifulSoup
from colorama import Fore, Back, Style
import urllib.parse as urlparse


class Google:
    def __init__(self, domain_root, proxy, output_file):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.source = "Google"
        self.results = Results(self.source)


    def run(self):
        logging.info("[*] starting Google query...")
        url = "https://www.google.com.au/search"
        params = {
            "q": f"site:{self.domain_root}",
            "filter": "0",
            "num": "100"
        }
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Safari/604.1.38",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Safari/604.1.38",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7"
        ]
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        eh = ErrorHandler()
        
        try:
            for i in range(0, 1001, 100):
                params["start"] = str(i)
                headers = {"User-Agent": random.choice(user_agents)}
                hh = HTTPHandler(headers=headers, proxies=proxies, params=params)
                response = hh.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "lxml")
                links = soup.findAll("a")
                if "did not match any documents" in soup.text:
                    break
                else:
                    for link in links:
                        href = link.get('href')
                        domain = urlparse.urlparse(href).netloc
                        domain = str(domain)
                        if (
                            domain.endswith("." + self.domain_root)
                            and domain not in self.results.data[self.source]["subdomains"]
                        ):
                            self.results.data[self.source]["subdomains"].add(domain)
                            logging.warning(f"{Fore.LIGHTGREEN_EX}[+] {domain}{Style.RESET_ALL}{Fore.WHITE} [Google]")
                self.normal_query()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logging.warning(f"{Fore.LIGHTYELLOW_EX}[!] [Google] 429 Too Many Requests, blocked by CAPTCHA")
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

    def normal_query(self):
        url = "https://www.google.com.au/search"
        normal_queries = ["homer", "marge", "bart", "lisa", "maggie"]
        normal_params = {"q": random.choice(normal_queries)}
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Safari/604.1.38",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Safari/604.1.38",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7"
        ]
        headers = {"User-Agent": random.choice(user_agents)}
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        eh = ErrorHandler()
        hh = HTTPHandler(headers=headers, proxies=proxies, params=normal_params)
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