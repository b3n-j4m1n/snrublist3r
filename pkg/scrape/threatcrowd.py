from bs4 import BeautifulSoup
from colorama import Fore, Back, Style
import logging
import requests


class ThreatCrowd:
    def __init__(self, domain_root, proxy):
        self.domain_root = domain_root
        self.proxy = {'http': proxy, "https": proxy}
        self.threatcrowd_results = set()

    def query(self, url, params):
        try:
            response = requests.get(url, params=params, proxies=self.proxy, verify=False)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(Fore.LIGHTRED_EX + "[-] ThreatCrowd Error: " + str(response.status_code) + " " + response.reason)
            return
        except requests.exceptions.RequestException as e:
            logging.error(Fore.LIGHTRED_EX + "[-] ThreatCrowd Error: " + str(e))
            return
        return response

    def run(self):
        logging.info("[*] starting ThreatCrowd query...")
        url = "https://www.threatcrowd.org/domain.php"
        params = {"domain": self.domain_root}
        response = self.query(url, params)
        if response is not None:
            try:
                soup = BeautifulSoup(response.text, "lxml")
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href')
                    href = str(href)
                    if href.endswith("." + self.domain_root)\
                    and "?domain=" in href:
                        domain = href.split('=')
                        logging.info(Fore.LIGHTGREEN_EX + "[+] " + domain[1])
                        self.threatcrowd_results.add(domain[1])
            except:
                pass

        logging.info("[*] " + str(len(self.threatcrowd_results)) + " subdomains from ThreatCrowd")
        return(self.threatcrowd_results)