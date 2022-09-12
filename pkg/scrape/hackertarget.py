from colorama import Fore, Back, Style
import logging
import requests


class HackerTarget:
    def __init__(self, domain_root, proxy):
        self.domain_root = domain_root
        self.proxy = {'http': proxy, "https": proxy}
        self.hackertarget_results = set()

    def query(self, url, headers, params):
        try:
            response = requests.get(url, headers=headers, params=params, proxies=self.proxy, verify=False)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(Fore.LIGHTRED_EX + "[-] Hacker Target Error: " + str(response.status_code) + " " + response.reason)
            return
        except requests.exceptions.RequestException as e:
            logging.error(Fore.LIGHTRED_EX + "[-] Hacker Target Error: " + str(e))
            return
        return response

    def run(self):
        logging.info("[*] starting Hacker Target query...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        url = "https://api.hackertarget.com/hostsearch/"
        params = {"q": self.domain_root}
        response = self.query(url, headers, params)
        if response is not None:
            try:
                line = response.text.split('\n')
                for l in line:
                    domain = l.split(',')[0]
                    if (
                        domain.endswith("." + self.domain_root)
                        and domain != self.domain_root
                    ):
                        logging.info(Fore.LIGHTGREEN_EX + "[+] " + domain)
                        self.hackertarget_results.add(domain)
            except:
                pass

        logging.info("[*] " + str(len(self.hackertarget_results)) + " subdomains from Hacker Target")
        return(self.hackertarget_results)