from bs4 import BeautifulSoup
from colorama import Fore, Back, Style
import json
import logging
import requests


class SonarSearch:
    def __init__(self, domain_root, proxy):
        self.domain_root = domain_root
        self.proxy = {'http': proxy, "https": proxy}
        self.sonarsearch_results = set()

    def query(self, url, headers):
        try:
            response = requests.get(url, headers=headers, proxies=self.proxy, verify=False)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(Fore.LIGHTRED_EX + "[-] SonarSearch Error: " + str(response.status_code) + " " + response.reason)
            return
        except requests.exceptions.RequestException as e:
            logging.error(Fore.LIGHTRED_EX + "[-] SonarSearch Error: " + str(e))
            return
        return response

    def run(self):
        logging.info("[*] starting SonarSearch search...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        url = (
            "https://sonar.omnisint.io/subdomains/"
            + self.domain_root
        )
        response = self.query(url, headers)
        if response is not None:
            try:
                soup = BeautifulSoup(response.text, "lxml")
                sonarsearch_json = json.loads(soup.text)
                for i in sonarsearch_json:
                    if i != self.domain_root:
                        self.sonarsearch_results.add(i)
                [logging.info(Fore.LIGHTGREEN_EX + "[+] " + i) for i in self.sonarsearch_results]
            except:
                pass

        logging.info("[*] " + str(len(self.sonarsearch_results)) + " subdomains from SonarSearch")
        return self.sonarsearch_results