from bs4 import BeautifulSoup
from colorama import Fore, Back, Style
import json
import logging
import requests


class Anubis:
    def __init__(self, domain_root, proxy):
        self.domain_root = domain_root
        self.proxy = {'http': proxy, "https": proxy}
        self.anubis_results = set()

    def query(self, url):
        try:
            response = requests.get(url, proxies=self.proxy, verify=False)
            if response.status_code == 300:
                logging.error(Fore.LIGHTRED_EX + "[-] Anubis Error: " + str(response.status_code) + " " + response.reason)
                return
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(Fore.LIGHTRED_EX + "[-] Anubis Error: " + str(response.status_code) + " " + response.reason)
            return
        except requests.exceptions.RequestException as e:
            logging.error(Fore.LIGHTRED_EX + "[-] Anubis Error: " + str(e))
            return
        return response

    def run(self):
        logging.info("[*] starting Anubis search...")
        url = (
            "https://jonlu.ca/anubis/subdomains/"
            + self.domain_root
        )
        response = self.query(url)
        if response is not None:
            try:
                soup = BeautifulSoup(response.text, "lxml")
                anubis_json = json.loads(soup.text)
                for result in anubis_json:
                    self.anubis_results.add(result)
                    logging.info(Fore.LIGHTGREEN_EX + "[+] " + result)
            except:
                pass

        logging.info("[*] " + str(len(self.anubis_results)) + " subdomains from Anubis")
        return(self.anubis_results)