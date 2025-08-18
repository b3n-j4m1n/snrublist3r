import logging
import re
import requests
import base64
import random
import time

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Back, Style


class VirusTotal:
    def __init__(self, domain_root, proxy, output_file):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.source = "Virus Total"
        self.results = Results(self.source)

    # credit https://www.cnblogs.com/gupingan/p/18452325
    def computeAntiAbuseHeader(self):
        e = time.time()
        n = 1e10 * (1 + random.random() % 5e4)
        raw = f'{n:.0f}-ZG9udCBiZSBldmls-{e:.3f}'
        res = base64.b64encode(raw.encode())
        return res.decode()

    def run(self):
        logging.info(f"[*] starting Virus Total search...")
        # credit - https://github.com/aboul3la/Sublist3r/pull/327 (obsolete now)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip',
            'Accept-Ianguage': 'en-US,en;q=0.8', # Ianguage not Language
            'X-Tool': 'vt-ui-main',
            'X-VT-Anti-Abuse-Header': self.computeAntiAbuseHeader()
        }
        url = (
        "https://www.virustotal.com/ui/domains/"
        + self.domain_root
        + "/subdomains?relationships=resolutions"
        )
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(headers=headers, proxies=proxies)
        eh = ErrorHandler()
        
        try:
            response = hh.get(url)
            response.raise_for_status()
            domains = re.findall(r"(?:(?:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})?)([\w-]+(?:\.[\w-]+)+)", response.text) # removes prepended IPs, e.g. 111.232.14.16mail.example.com
            for domain in domains:
                if domain.startswith("*"):
                    domain = domain[2:] # remove the "*."
                if (
                    domain.endswith("." + self.domain_root)
                    and domain not in self.results.data[self.source]["subdomains"]
                ):
                    self.results.data[self.source]["subdomains"].add(domain)
                    logging.info(f"{Fore.LIGHTGREEN_EX}[+] {domain}{Style.RESET_ALL}{Fore.WHITE} [Virus Total]")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logging.warning(f"{Fore.LIGHTYELLOW_EX}[!] [VirusTotal] 429 reCAPTCHA validation failed, please try again")
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