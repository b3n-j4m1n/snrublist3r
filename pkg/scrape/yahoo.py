from bs4 import BeautifulSoup
from colorama import Fore, Back, Style
import logging
import requests


class Yahoo:
    def __init__(self, domain_root, proxy):
        self.domain_root = domain_root
        self.proxy = {'http': proxy, "https": proxy}
        self.yahoo_results = set()

    def query(self, url, headers, params):
        try:
            response = requests.get(url, params=params, headers=headers, proxies=self.proxy, verify=False)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(Fore.LIGHTRED_EX + "[-] Yahoo Error: " + str(response.status_code) + " " + response.reason)
            return
        except requests.exceptions.RequestException as e:
            logging.error(Fore.LIGHTRED_EX + "[-] Yahoo Error: " + str(e))
            return
        return response

    def run(self):
        logging.info("[*] starting Yahoo search...")
        headers = headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        url = "https://search.yahoo.com/search"
        params = {"p": "site:" + self.domain_root, "xargs": 0}
        for i in range(1, 101, 9):
            params["b"] = str(i)
            response = self.query(url, headers, params)
            if response is not None:
                try:
                    soup = BeautifulSoup(response.text, "lxml")
                    if "We did not find results for" in soup.text:
                        break
                    links = soup.find_all(attrs={"class": "d-ib p-abs t-0 l-0 fz-14 lh-20 fc-obsidian wr-bw ls-n pb-4"})
                    for link in links:
                        domain = link.text.split(" ")[0]
                        if domain.endswith("." + self.domain_root)\
                        and domain != self.domain_root\
                        and domain not in self.yahoo_results:
                            logging.info(Fore.LIGHTGREEN_EX + "[+] " + domain)
                            self.yahoo_results.add(domain)
                except:
                    pass

        logging.info("[*] " + str(len(self.yahoo_results)) + " subdomains from Yahoo")
        return(self.yahoo_results)