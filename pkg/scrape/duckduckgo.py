import logging
import re
import requests
import time

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Back, Style


class DuckDuckGo:
    def __init__(self, domain_root, proxy, output_file):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.source = "DuckDuckGo"
        self.results = Results(self.source)
  

    def get_param(self):
        url = "https://duckduckgo.com/"
        params = {"q": "site:" + self.domain_root}
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(headers=headers, proxies=proxies, params=params)
        eh = ErrorHandler()

        try:
            response = hh.get(url)
            vqd_param = re.search(r'vqd="([^"]+)"', response.text).group(1)
        except IndexError as e:
            logging.debug(f"{Fore.LIGHTRED_EX}[ERROR] {self.source}{Style.RESET_ALL} IndexError {str(e)}")
            return None
        except (
            requests.exceptions.RequestException, 
            NameError, 
            ConnectionError,
            TypeError, 
            AttributeError, 
            KeyboardInterrupt
            ) as e:
            eh.handle_error(e, self.source)
            return None
        return vqd_param
    
    def run(self):
        logging.info("[*] starting DuckDuckGo query...")
        url = "https://links.duckduckgo.com/d.js"
        vqd_param = self.get_param()
        if vqd_param is None:
            logging.warning(f"{Fore.LIGHTYELLOW_EX}[!] [DuckDuckGo] error getting vqd parameter")
            return self.results.data
        params = {
            "q": "site:" + self.domain_root,
            "kl": "wt-wt", # no region
            "vqd": vqd_param,
            "sp": "0", # disable spellcheck
            "ex": "-2" # safe search off
        }
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(headers=headers, proxies=proxies, params=params)
        eh = ErrorHandler()
        try:
            for i in range(0, 500, 20):
                params["s"] = str(i)
                response = hh.get(url=url)
                response.raise_for_status()
                if response.history:
                    for resp in response.history:
                        if resp.status_code == 301:
                            logging.warning(f"{Fore.LIGHTYELLOW_EX}[!] [DuckDuckGo] rate-limiting detected")
                            return self.results.data
                domains = re.findall(r'(?:%252F|//|@)((?:[\w-]+[.])+[\w-]+)', response.text)
                for domain in domains:
                    if (
                        domain.endswith("." + self.domain_root)
                        and domain not in self.results.data[self.source]["subdomains"]
                    ):
                        self.results.data[self.source]["subdomains"].add(domain)
                        logging.warning(f"{Fore.LIGHTGREEN_EX}[+] {domain}{Style.RESET_ALL}{Fore.WHITE} [DuckDuckGo]")
                time.sleep(10)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 418:
                logging.debug(f"{Fore.LIGHTYELLOW_EX}[!] [DuckDuckGo] 429 I'm a teapot")
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