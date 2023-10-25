import logging
import requests

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from bs4 import BeautifulSoup
from colorama import Fore, Back, Style


class DNSDumpster:
    def __init__(self, domain_root, proxy, output_file):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.source = "DNSDumpster"
        self.results = Results(self.source)


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
        url = f"https://dnsdumpster.com/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(headers=headers, proxies=proxies)
        eh = ErrorHandler()
        try:
            csrf_response = hh.get(url)
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
            logging.error(Fore.LIGHTRED_EX + "[-] [DNSDumpster] error handling CSRF data")
            return self.results.data
        
        hh = HTTPHandler(headers=headers, proxies=proxies, data=data)
        try:
            response = hh.post(url)
            soup = BeautifulSoup(response.text, "lxml")
            links = soup.findAll("a")
            for link in links:
                href = link.get('href')
                href = str(href)
                if href.endswith("." + self.domain_root):
                    domain = href.split('//')
                    logging.info(f"{Fore.LIGHTGREEN_EX}[+] {domain[2]}{Style.RESET_ALL}{Fore.WHITE} [DNSDumpster]")
                    self.results.data[self.source]["subdomains"].add(domain[2])
        except (
            requests.exceptions.RequestException, 
            NameError,
            ConnectionError,
            TypeError, 
            AttributeError, 
            KeyboardInterrupt
            ) as e:
            eh.handle_error(e, self.source)

        if self.output_file:
            oh = OutputHandler()
            oh.handle_output(self.output_file, self.results.data)

        return self.results.data