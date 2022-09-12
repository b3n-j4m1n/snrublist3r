from colorama import Fore, Back, Style
import logging
import re
import requests


class Bing:
    def __init__(self, domain_root, proxy):
        self.domain_root = domain_root
        self.proxy = {'http': proxy, "https": proxy}
        self.bing_results = set()

    def query(self, url, headers, params):
        try:
            response = requests.get(url, headers=headers, params=params, proxies=self.proxy, verify=False)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(Fore.LIGHTRED_EX + "[-] Bing Error: " + str(response.status_code) + " " + response.reason)
            return
        except requests.exceptions.RequestException as e:
            logging.error(Fore.LIGHTRED_EX + "[-] Bing Error: " + str(e))
            return
        return response

    def run(self):
        logging.info("[*] starting Bing query...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        url = "https://www.bing.com/search"
        params = {"q": "site:" + self.domain_root, "pn": self.domain_root}
        for i in range(1, 200, 10):
            params["first"] = str(i)
            response = self.query(url, headers, params)
            if response is not None:
                try:
                    if "There are no results for" in response.text:
                        return self.bing_results
                    else:
                        domains = re.findall(r"(?:[\w-]+[.])+[\w-]+", response.text)
                        for domain in domains:
                            if (
                                domain.endswith("." + self.domain_root)
                                and domain != self.domain_root
                                and domain not in self.bing_results
                            ):
                                logging.info(Fore.LIGHTGREEN_EX + "[+] " + domain)
                                self.bing_results.add(domain)
                except:
                    pass

        logging.info("[*] " + str(len(self.bing_results)) + " subdomains from Bing")
        return self.bing_results
