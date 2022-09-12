from bs4 import BeautifulSoup
from colorama import Fore, Back, Style
import json
import logging
import requests


class AlienVault:
    def __init__(self, domain_root, proxy):
        self.domain_root = domain_root
        self.proxy = {'http': proxy, "https": proxy}
        self.alienvault_results = set()

    def query(self, url, headers):
        try:
            response = requests.get(url, headers=headers, proxies=self.proxy, verify=False)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(Fore.LIGHTRED_EX + "[-] AlientVault Error: " + str(response.status_code) + " " + response.reason)
            return
        except requests.exceptions.RequestException as e:
            logging.error(Fore.LIGHTRED_EX + "[-] AlientVault Error: " + str(e))
            return
        return response

    def run(self):
        logging.info("[*] starting AlienVault query...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        url = (
            "https://otx.alienvault.com/api/v1/indicators/domain/"
            + self.domain_root
            + "/passive_dns"
        )
        response = self.query(url, headers)
        if response is not None:
            try:
                soup = BeautifulSoup(response.text, "lxml")
                alienvault_json = json.loads(soup.text)
                for domain in alienvault_json["passive_dns"]:
                    if (
                        domain["hostname"].endswith("." + self.domain_root)
                        and domain["hostname"] not in self.alienvault_results
                        and domain["hostname"] != self.domain_root
                    ):
                        logging.info(Fore.LIGHTGREEN_EX + "[+] " + domain["hostname"])
                        self.alienvault_results.add(domain["hostname"])
            except:
                pass
        
        logging.info("[*] " + str(len(self.alienvault_results)) + " subdomains from AlienVault")
        return self.alienvault_results