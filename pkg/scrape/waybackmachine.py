from colorama import Fore, Back, Style
import logging
import re
import requests


class WaybackMachine:
    def __init__(self, domain_root, proxy):
        self.domain_root = domain_root
        self.proxy = {'http': proxy, "https": proxy}
        self.waybackmachine_results = set()

    def query(self, url, params, headers):
        try:
            response = requests.get(url, params=params, headers=headers, proxies=self.proxy, verify=False)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(Fore.LIGHTRED_EX + "[-] Wayback Machine Error: " + str(response.status_code) + " " + response.reason)
            return
        except requests.exceptions.RequestException as e:
            logging.error(Fore.LIGHTRED_EX + "[-] Wayback Machine Error: " + str(e))
            return
        return response

    def run(self):
        logging.info("[*] starting Wayback Machine query...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        url = "http://web.archive.org/cdx/search/cdx"
        params = {
            "url": "*." + self.domain_root + "/*",
            "output": "txt",
            "fl": "original",
            "collapse": "urlkey",
        }
        response = self.query(url, params=params, headers=headers)
        if response is not None:
            try:
                domains = re.findall(r'(?:%252F|//|@)((?:[\w-]+[.])+[\w-]+)', response.text)
                for domain in domains:
                    if (
                        self.domain_root in domain
                        and domain not in self.waybackmachine_results
                        and domain != self.domain_root
                    ):
                        logging.info(Fore.LIGHTGREEN_EX + "[+] " + domain)
                        self.waybackmachine_results.add(domain)
            except:
                pass

        logging.info("[*] " + str(len(self.waybackmachine_results)) + " subdomains from the Wayback Machine")
        return(self.waybackmachine_results)