from colorama import Fore, Back, Style
import logging
import re
import requests


class DuckDuckGo:
    def __init__(self, domain_root, proxy):
        self.domain_root = domain_root
        self.proxy = {'http': proxy, "https": proxy}
        self.duckduckgo_results = set()
  
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

    def get_cookie(self):
        url = "https://duckduckgo.com/"
        params = {"q": "site:" + self.domain_root, "t": "ha", "va": "j"}
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        cookie_response = self.query(url, headers, params)
        try:
            cookie = re.findall(r"vqd='([0-9]+(-[0-9]+)+)'", cookie_response.text)[0][0]
        except IndexError as e:
            logging.error(Fore.LIGHTRED_EX + "[-] " + str(e))
        return cookie
    
    def run(self):
        logging.info("[*] starting DuckDuckGo query...")
        url = "https://links.duckduckgo.com/d.js"
        try:
            cookie = self.get_cookie()
            params = {
                "q": "site:" + self.domain_root,
                "kl": "wt-wt",
                "l": "us-en",
                "a": "ha",
                "dl": "en",
                "ss_mkt": "us",
                "vqd": cookie,
                "p_ent": "",
                "ex": "-1",
                "sp": "1",
                "biaexp": "b",
                "msvrtexp": "b",
                "eclsexp": "b",
                "wrap": "1",
                "bpa": "1",
            }
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
            url ="https://duckduckgo.com/d.js"
            for i in range(0, 500, 20):
                params["s"] = str(i)
                response = requests.get(url, params=params, headers=headers, proxies=self.proxy, verify=False)
                domains = re.findall(r'(?:%252F|//|@)((?:[\w-]+[.])+[\w-]+)', response.text)
                for domain in domains:
                    if (
                        domain.endswith(self.domain_root)
                        and domain != self.domain_root
                        and domain not in self.duckduckgo_results
                    ):
                        logging.info(Fore.LIGHTGREEN_EX + "[+] " + domain)
                        self.duckduckgo_results.add(domain)
        except (IndexError, AttributeError, UnboundLocalError):
            pass


        logging.info("[*] " + str(len(self.duckduckgo_results)) + " subdomains from DuckDuckGo")
        return self.duckduckgo_results