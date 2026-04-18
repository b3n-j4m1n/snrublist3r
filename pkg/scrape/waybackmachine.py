import logging
import re
import requests

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Back, Style


class WaybackMachine:
    def __init__(self, domain_root, proxy, output_file):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.source = "Wayback Machine"
        self.timeout = 180
        self.results = Results(self.source)


    def run(self):
        logging.warning(f"[*] starting Wayback Machine search...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        url = "http://web.archive.org/cdx/search/cdx"
        params = {
            "url": "*." + self.domain_root + "/*",
            "output": "txt",
            "fl": "original",
            "collapse": "urlkey",
        }
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(headers=headers, proxies=proxies, params=params, timeout=self.timeout)
        eh = ErrorHandler()

        try:
            response = hh.get(url)
            domains = re.findall(r'(?:%252F|//|@)((?:[\w-]+[.])+[\w-]+)', response.text, flags=re.IGNORECASE)
            for domain in domains:
                if domain.startswith("2f"):
                    domain = domain[2:]
                domain = domain.lower() # preventing different case duplicates
                if (
                    domain.endswith("." + self.domain_root)
                    and domain not in self.results.data[self.source]["subdomains"]
                ):
                    self.results.data[self.source]["subdomains"].add(domain)
                    logging.info(f"{Fore.LIGHTGREEN_EX}[+] {domain}{Style.RESET_ALL}{Fore.WHITE} [Wayback Machine]")
        except requests.exceptions.Timeout as e:
            logging.debug(f"{Fore.LIGHTYELLOW_EX}[!] [Wayback Machine] timed out - service may be slow or unavailable{Style.RESET_ALL}")
            eh.handle_error(e, self.source)
        except requests.exceptions.ConnectionError as e:
            logging.debug(f"{Fore.LIGHTYELLOW_EX}[!] [Wayback Machine] connection failed - service may be unavailable{Style.RESET_ALL}")
            eh.handle_error(e, self.source)
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