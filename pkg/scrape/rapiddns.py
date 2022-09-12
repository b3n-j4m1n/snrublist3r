from colorama import Fore, Back, Style
import logging
import re
import requests


class RapidDNS:
    def __init__(self, domain_root, proxy):
        self.domain_root = domain_root
        self.proxy = {'http': proxy, "https": proxy}
        self.rapiddns_results = set()

    def query(self, url, headers):
        try:
            response = requests.get(url, headers=headers, proxies=self.proxy, verify=False)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(Fore.LIGHTRED_EX + "[-] RapidDNS Error: " + str(response.status_code) + " " + response.reason)
            return
        except requests.exceptions.RequestException as e:
            logging.error(Fore.LIGHTRED_EX + "[-] RapidDNS Error: " + str(e))
            return
        return response

    def run(self):
        logging.info("[*] starting RapidDNS query...")
        url = (
            "https://rapiddns.io/subdomain/"
            + self.domain_root
            + "?full=1"
        )
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        response = self.query(url, headers)
        if response is not None:
            try:
                domains = re.findall(r"(?:[\w-]+[.])+[\w-]+", response.text)
                for domain in domains:
                    if (
                        domain.endswith("." + self.domain_root)
                        and domain != self.domain_root
                        and domain not in self.rapiddns_results
                    ):
                        logging.info(Fore.LIGHTGREEN_EX + "[+] " + domain)
                        self.rapiddns_results.add(domain)
            except:
                pass
        logging.info("[*] " + str(len(self.rapiddns_results)) + " subdomains from RapidDNS")
        return self.rapiddns_results