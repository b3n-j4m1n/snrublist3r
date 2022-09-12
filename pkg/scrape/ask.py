from bs4 import BeautifulSoup
from colorama import Fore, Back, Style
import logging
import requests
import urllib.parse as urlparse


class Ask:
    def __init__(self, domain_root, proxy):
        self.domain_root = domain_root
        self.proxy = {'http': proxy, "https": proxy}
        self.ask_results = set()

    def query(self, url, headers, params):
        try:
            response = requests.get(url, headers=headers, params=params, proxies=self.proxy, verify=False)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(Fore.LIGHTRED_EX + "[-] Ask Error: " + str(response.status_code) + " " + response.reason)
            return
        except requests.exceptions.RequestException as e:
            logging.error(Fore.LIGHTRED_EX + "[-] Ask Error: " + str(e))
            return
        return response

    def run(self):
        logging.info("[*] starting Ask query...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        url = "https://www.ask.com/web"
        params = {"q": self.domain_root}
        for i in range(1, 5):
            params["page"] = str(i)
            response = self.query(url, headers, params)
            if response is not None:
                try:
                    soup = BeautifulSoup(response.text, "lxml")
                    links = soup.findAll("a")
                    for link in links:
                        href = link.get("href")
                        domain = urlparse.urlparse(href).netloc
                        domain = str(domain)
                        if (
                            domain.endswith("." + self.domain_root)
                            and domain not in self.ask_results
                            and domain != self.domain_root
                        ):
                            self.ask_results.add(domain)
                            logging.info(Fore.LIGHTGREEN_EX + "[+] " + domain)
                except:
                    pass

        logging.info("[*] " + str(len(self.ask_results)) + " subdomains from Ask")
        return self.ask_results
