from bs4 import BeautifulSoup
from colorama import Fore, Back, Style
import logging
import re
import requests
import time


class Gist:
    def __init__(self, domain_root, proxy):
        self.domain_root = domain_root
        self.proxy = {'http': proxy, "https": proxy}
        self.gist_links = set()
        self.gist_results = set()

    def query(self, url, headers, params):
        try:
            response = requests.get(url, headers=headers, params=params, proxies=self.proxy, verify=False)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(Fore.LIGHTRED_EX + "[-] Gist Error: " + str(response.status_code) + " " + response.reason)
            return
        except requests.exceptions.RequestException as e:
            logging.error(Fore.LIGHTRED_EX + "[-] Gist Error: " + str(e))
            return
        return response

    def run(self):
        logging.info("[*] starting Gist query...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        url = "https://gist.github.com/search"
        params = {"q": "\"" + self.domain_root + "\"", "ref": "searchresults"}
        for i in range(1, 101):
            params["p"] = str(i)
            response = self.query(url, headers, params)
            try:
                soup = BeautifulSoup(response.text, "lxml")
                if "We couldn’t find any gists matching" in soup.text:
                    break
                gists = soup.findAll(attrs={"class": "link-overlay"})
                for gist in gists:
                    href = gist.get('href')
                    self.gist_links.add(href)
                time.sleep(4)
            except:
                pass
        
        for link in self.gist_links:
            url = link
            response = requests.get(url, headers=headers, proxies=self.proxy, verify=False)
            try:
                domains = re.findall(r"(?:[\w-]+[.])+[\w-]+", response.text)
                for domain in domains:
                    if (
                        domain.endswith("." + self.domain_root)
                        and domain != self.domain_root
                        and domain not in self.gist_results
                    ):
                        logging.info(Fore.LIGHTGREEN_EX + "[+] " + domain)
                        self.gist_results.add(domain)
            except:
                pass

        logging.info("[*] " + str(len(self.gist_results)) + " subdomains from Gist")
        return(self.gist_results)