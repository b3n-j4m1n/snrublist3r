from bs4 import BeautifulSoup
from colorama import Fore, Back, Style
import logging
import random
import requests
import time
import urllib.parse as urlparse


class Google:
    def __init__(self, domain_root, proxy, autopilot):
        self.domain_root = domain_root
        self.proxy = {'http': proxy, "https": proxy}
        self.autopilot = autopilot
        self.google_results = set()

    def query(self, url, headers, params):
        try:
            response = requests.get(url, headers=headers, params=params, proxies=self.proxy, verify=False)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(Fore.LIGHTRED_EX + "[-] Google Error: " + str(response.status_code) + " " + response.reason)
            return
        except requests.exceptions.RequestException as e:
            logging.error(Fore.LIGHTRED_EX + "[-] Google Error: " + str(e))
            return
        return response

    def run(self):
        logging.info("[*] starting Google query...")
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Safari/604.1.38",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Safari/604.1.38",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7"
        ]
        normal_queries = ["homer", "marge", "bart", "lisa", "maggie"]
        url = "https://www.google.com.au/search"
        params = {"q": "site:" + self.domain_root, "filter": "0", "num": "100"}
        for i in range(0, 1001, 100):
            params["start"] = str(i)
            headers = {"User-Agent": random.choice(user_agents)}
            normal_params = {"q": random.choice(normal_queries)}
            response = self.query(url, headers, params)
            if response is not None:
                if response.status_code == 429:
                    logging.warning(Fore.LIGHTYELLOW_EX + "[!] 429 Too Many Requests, blocked by CAPTCHA")
                    if self.autopilot:
                        break
                    else:
                        print(Fore.LIGHTYELLOW_EX + "[?] continue (y) or skip (s)? [wait or change proxy before resuming]: ", end='') # input() doesn't work with colorama
                        captcha_prompt = input()
                        if captcha_prompt == ("s"):
                            break
                        elif captcha_prompt != ("y"):
                            logging.error(Fore.LIGHTRED_EX + "[-] invalid response")
                            break
                        continue
                try:
                    soup = BeautifulSoup(response.text, "lxml")
                    links = soup.findAll("a")
                    if "did not match any documents" in soup.text:
                        break
                    else:   
                        for link in links:
                            href = link.get('href')
                            domain = urlparse.urlparse(href).netloc
                            domain = str(domain)
                            if (
                                domain.endswith("." + self.domain_root)
                                and domain not in self.google_results
                                and domain != self.domain_root
                            ):
                                logging.info(Fore.LIGHTGREEN_EX + "[+] " + domain)
                                self.google_results.add(domain)
                    requests.get(url, params=normal_params, headers=headers, proxies=self.proxy, verify=False)
                    time.sleep(random.randint(3, 7))
                except:
                    pass

        logging.info("[*] " + str(len(self.google_results)) + " subdomains from Google")
        return(self.google_results)