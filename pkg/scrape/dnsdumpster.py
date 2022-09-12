from bs4 import BeautifulSoup
from colorama import Fore, Back, Style
import logging
import requests


class DNSDumpster:
    def __init__(self, domain_root, proxy):
        self.domain_root = domain_root
        self.proxy = {'http': proxy, "https": proxy}
        self.dnsdumpster_results = set()
  
    def query(self, url, headers):
        try:
            response = requests.get(url, headers=headers, proxies=self.proxy, verify=False)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(Fore.LIGHTRED_EX + "[-] DNSDumpster Error: " + str(response.status_code) + " " + response.reason)
            return
        except requests.exceptions.RequestException as e:
            logging.error(Fore.LIGHTRED_EX + "[-] DNSDumpster Error: " + str(e))
            return
        return response

    def get_csrf_data(self, response):
        data = {}
        soup = BeautifulSoup(response.text, "lxml")
        csrfmiddlewaretoken = soup.find("input", {"name":"csrfmiddlewaretoken"})
        data.update(
            {
                "csrftoken": response.cookies["csrftoken"],
                "csrfmiddlewaretoken_value": csrfmiddlewaretoken["value"],
            }
        )
        return data
    
    def run(self):
        logging.info("[*] starting DNSDumpster query...")
        url = "https://dnsdumpster.com/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        csrf_response = self.query(url, headers)
        try:
            csrf_data = self.get_csrf_data(csrf_response)
            csrftoken = csrf_data["csrftoken"]
            headers.update(
                {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": "https://dnsdumpster.com/",
                    "Cookie": "csrftoken=" + csrftoken,
                }
            )
            csrfmiddlewaretoken_value = csrf_data["csrfmiddlewaretoken_value"]
            data = {
                "csrfmiddlewaretoken": csrfmiddlewaretoken_value,
                "targetip": self.domain_root,
                "user": "free",
            }
        except:
            logging.error(Fore.LIGHTRED_EX + "[-] error handling csrf data")
            return self.dnsdumpster_results
        response = requests.post(url, data=data, headers=headers, proxies=self.proxy, verify=False)
        try:
            soup = BeautifulSoup(response.text, "lxml")
            links = soup.findAll("a")
            for link in links:
                href = link.get('href')
                href = str(href)
                if href.endswith("." + self.domain_root):
                    domain = href.split('//')
                    logging.info(Fore.LIGHTGREEN_EX + "[+] " + domain[2])
                    self.dnsdumpster_results.add(domain[2])
        except:
            pass

        logging.info("[*] " + str(len(self.dnsdumpster_results)) + " subdomains from DNSDumpster")
        return self.dnsdumpster_results