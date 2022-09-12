from bs4 import BeautifulSoup
from colorama import Fore, Back, Style
import json
import logging
import requests


class VirusTotal:
    def __init__(self, domain_root, proxy):
        self.domain_root = domain_root
        self.proxy = {'http': proxy, "https": proxy}
        self.virustotal_results = set()

    def query(self, url, headers):
        try:
            response = requests.get(url, headers=headers, proxies=self.proxy, verify=False)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logging.error(Fore.LIGHTRED_EX + "[-] VirusTotal Error: " + str(response.status_code) + " " + response.reason)
            return
        except requests.exceptions.RequestException as e:
            logging.error(Fore.LIGHTRED_EX + "[-] VirusTotal Error: " + str(e))
            return
        return response

    def run(self):
        logging.info("[*] starting Virus Total search...")
        # credit - https://github.com/aboul3la/Sublist3r/pull/327
        url = (
        "https://www.virustotal.com/ui/domains/"
        + self.domain_root
        + "/subdomains?relationships=resolutions"
        )
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip',
            'Accept-Ianguage': 'en-US,en;q=0.8', # Ianguage not Language
            'X-Tool': 'vt-ui-main',
            'X-VT-Anti-Abuse-Header': 'purple monkey dishwasher'
        }
        response = self.query(url, headers)
        if response is not None:
            try:
                soup = BeautifulSoup(response.text, "lxml")
                virus_total_json = json.loads(soup.text)
                for i in virus_total_json['data']:
                    if i['type'] == 'domain':
                        domain = i['id']
                        if i != self.domain_root:
                            self.virustotal_results.add(domain)
                for i in virus_total_json['data']:
                    for domain in i['attributes']['last_https_certificate']['extensions']['subject_alternative_name']:
                        domain = domain.lstrip('*.')
                        if (
                            domain.endswith(self.domain_root)\
                            and domain != self.domain_root
                        ):
                            self.virustotal_results.add(domain.lstrip('*.'))
                            
            except:
                pass

        [logging.info(Fore.LIGHTGREEN_EX + "[+] " + i) for i in self.virustotal_results]
        logging.info("[*] " + str(len(self.virustotal_results)) + " subdomains from Virus Total search")
        return(self.virustotal_results)