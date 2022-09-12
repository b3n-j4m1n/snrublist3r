from bs4 import BeautifulSoup
from colorama import Fore, Back, Style
import logging
import requests

class CertificateSearch:
    def __init__(self, domain_root, proxy):
        self.domain_root = domain_root
        self.proxy = {'http': proxy, "https": proxy}
        self.certificate_search_results = set()

    def query(self, url, params):
        try:
            response = requests.get(url, params=params, proxies=self.proxy, verify=False)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(Fore.LIGHTRED_EX + "[-] Certificate Search Error: " + str(response.status_code) + " " + response.reason)
            return
        except requests.exceptions.RequestException as e:
            logging.error(Fore.LIGHTRED_EX + "[-] Certificate Search Error: " + str(e))
            return
        return response 

    def run(self):
        logging.info("[*] starting certificate transparency search...")
        url = "https://crt.sh"
        params = {"q": self.domain_root}
        response = self.query(url, params)
        if response is not None:
            try:
                soup = BeautifulSoup(response.text, "lxml")
                data = soup.findAll("td")
                if (
                    "Sorry, something went wrong..." in soup.text
                    or "a padding to disable MSIE and Chrome friendly error page" in soup.text
                ):
                    logging.error(Fore.LIGHTRED_EX + "[-] something went wrong in certificate transparency search, please try again later")
                else:
                    for value in data:
                        value_list = value.get_text(strip=True, separator="\n").splitlines() # handling data such as <td>example.com<br>uat.example.com</tr>
                        for i in value_list:
                            if (
                                i.endswith("." + self.domain_root)
                                and not i.startswith("*")
                                and i != self.domain_root
                            ):
                                self.certificate_search_results.add(i)
                [logging.info(Fore.LIGHTGREEN_EX + "[+] " + i) for i in self.certificate_search_results]
            except:
                pass
            
        logging.info("[*] " + str(len(self.certificate_search_results)) + " subdomains from certificate transparency search")
        return(self.certificate_search_results)