from bs4 import BeautifulSoup
from colorama import Fore, Back, Style
import json
import logging
import requests


class ThreatMiner:
    def __init__(self, domain_root, proxy):
        self.domain_root = domain_root
        self.proxy = {'http': proxy, "https": proxy}
        self.threatminer_results = set()

    def query(self, url, headers, params):
        try:
            response = requests.get(url, params=params, headers=headers, proxies=self.proxy, verify=False)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(Fore.LIGHTRED_EX + "[-] " + str(response.status_code) + " " + response.reason)
            return
        except requests.exceptions.RequestException as e:
            logging.error(Fore.LIGHTRED_EX + "[-] " + str(e))
            return
        return response

    def run(self):
        logging.info("[*] starting ThreatMiner query...")
        url = "https://api.threatminer.org/v2/domain.php"
        params = {"q": self.domain_root, "rt": "5"}
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        response = self.query(url, headers, params)
        if response is not None:
            try:
                soup = BeautifulSoup(response.text, "lxml")
                threatminer_json = json.loads(soup.text)
                for domain in threatminer_json['results']:
                    logging.info(Fore.LIGHTGREEN_EX + "[+] " + domain)
                    self.threatminer_results.add(domain)
            except:
                pass

        logging.info("[*] " + str(len(self.threatminer_results)) + " subdomains from ThreatMiner")
        return self.threatminer_results