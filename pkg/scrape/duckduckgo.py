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
  

    def get_deep_preload_link(self):
        url = "https://duckduckgo.com/"
        params = {"q": "site:" + self.domain_root}
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(headers=headers, proxies=proxies, params=params)
        eh = ErrorHandler()

        try:
            response = hh.get(url)
            if response.status_code == 202:
                return "RATE_LIMITED_202"
            deep_preload_link = re.search(r'<link[^>]+id="deep_preload_link"[^>]+href="([^"]+)"', response.text).group(1)
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
        return deep_preload_link
    
    def run(self):
        logging.warning("[*] starting DuckDuckGo query...")
        deep_preload_link = self.get_deep_preload_link() # the "more results" link
        if deep_preload_link == "RATE_LIMITED_202":
            logging.debug(f"{Fore.LIGHTYELLOW_EX}[!] [DuckDuckGo] 202 rate-limiting detected")
            return self.results.data
        elif deep_preload_link is None:
            logging.debug(f"{Fore.LIGHTYELLOW_EX}[!] [DuckDuckGo] error getting deep_preload_link")
            return self.results.data
        base_url = "https://links.duckduckgo.com"
        params = deep_preload_link.replace("https://links.duckduckgo.com", "")
        headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0",
                    #"Accept": "*/*",
                    #"Accept-Language": "en-US,en;q=0.5",
                    #"Accept-Encoding": "gzip, deflate, br",
                    #"Referer": "https://duckduckgo.com/",
                    #"DNT": "1",
                    #"Sec-GPC": "1",
                    #"Sec-Fetch-Dest": "script",
                    "Sec-Fetch-Mode": "no-cors",
                    "Sec-Fetch-Site": "same-site",
                    "Priority": "u=1",
                    #"TE": "trailers"
                }
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(headers=headers, proxies=proxies)
        eh = ErrorHandler()
        try:
            for i in range(10):
                url = base_url + params
                response = hh.get(url=url)
                response.raise_for_status()
                if response.status_code == 202:
                    logging.debug(f"{Fore.LIGHTYELLOW_EX}[!] [DuckDuckGo] 202 rate-limiting detected")
                    return self.results.data
                domains = re.findall(r'(?:%252F|//|@)((?:[\w-]+[.])+[\w-]+)', response.text, flags=re.IGNORECASE)
                for domain in domains:
                    if (
                        domain.endswith("." + self.domain_root)
                        and domain not in self.results.data[self.source]["subdomains"]
                    ):
                        self.results.data[self.source]["subdomains"].add(domain)
                        logging.info(f"{Fore.LIGHTGREEN_EX}[+] {domain}{Style.RESET_ALL}{Fore.WHITE} [DuckDuckGo]")
                more_results = re.search(r'{"n":"(/d\.js\?[^"]+)"', response.text)
                if not more_results:
                    break
                params = more_results.group(1)
                time.sleep(10)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 418:
                logging.debug(f"{Fore.LIGHTYELLOW_EX}[!] [DuckDuckGo] 429 I'm a teapot")
            return self.results.data
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