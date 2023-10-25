import logging
import requests

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Back, Style


class HackerTarget:
    def __init__(self, domain_root, proxy, output_file):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.source = "Hacker Target"
        self.results = Results(self.source)


    def run(self):
        logging.warning(f"[*] starting Hacker Target query...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        url = f"https://api.hackertarget.com/hostsearch/"
        params = {
            "q": f"{self.domain_root}"
        }
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(headers=headers, proxies=proxies, params=params)
        eh = ErrorHandler()
        
        try:
            response = hh.get(url)
            if "API count exceeded" in response.text:
                logging.warning(f"{Fore.LIGHTYELLOW_EX}[!] [Hacker Targer] 200 API count exceeded")
                return self.results.data
            line = response.text.split('\n')
            for l in line:
                    domain = l.split(',')[0]
                    if (
                        domain.endswith("." + self.domain_root)
                        and domain not in self.results.data[self.source]["subdomains"]
                    ):
                        self.results.data[self.source]["subdomains"].add(domain)
                        logging.info(f"{Fore.LIGHTGREEN_EX}[+] {domain}{Style.RESET_ALL}{Fore.WHITE} [HackerTarget]")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logging.warning(f"{Fore.LIGHTYELLOW_EX}[!] [Hacker Target] 429 Too Many Requests")
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