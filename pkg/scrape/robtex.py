import logging
import json
import re
import time
import requests

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.filter_handler import is_filtered
from pkg.utils.http_handler import HTTPHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Style


class Robtex:
    def __init__(self, domain_root, proxy, output_file, filter_strings=None):
        self.domain_root = domain_root
        self.output_file = output_file
        self.proxy = proxy
        self.filter_strings = filter_strings
        self.source = "Robtex"
        self.results = Results(self.source)

    REVERSE_IP_LIMIT = 10
    MAX_LABELS = 6 # Robtex data contains mangled multi-hostname concatenations, junk runs deeper than this

    @staticmethod
    def plausible_hostname(hostname):
        labels = hostname.split(".")
        if len(labels) > Robtex.MAX_LABELS:
            return False
        for label in labels:
            if not label or len(label) > 63 or not re.match(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", label):
                return False
        for index, label_a in enumerate(labels):
            for label_b in labels[index + 1:]:
                common = 0
                for a, b in zip(label_a, label_b):
                    if a != b:
                        break
                    common += 1
                if common >= 6:
                    return False
        return True

    def run(self):
        logging.warning(f"[*] starting Robtex query...")
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None
        hh = HTTPHandler(proxies=proxies, timeout=60)
        eh = ErrorHandler()

        try:
            url = "https://freeapi.robtex.com/pdns/forward/" + self.domain_root
            response = hh.get(url)
            response.raise_for_status()
            ips = set()
            for line in response.text.splitlines():
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.decoder.JSONDecodeError:
                    continue
                if isinstance(record, dict) and record.get("rrtype") in ("A", "AAAA"):
                    ip = record.get("rrdata", "")
                    if ip:
                        ips.add(ip)
            for index, ip in enumerate(sorted(ips)):
                if index >= self.REVERSE_IP_LIMIT:
                    break
                if index > 0:
                    time.sleep(1.1) # free API rate limit, ~1 request/second
                response = hh.get("https://freeapi.robtex.com/pdns/reverse/" + ip)
                response.raise_for_status()
                for line in response.text.splitlines():
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                    except json.decoder.JSONDecodeError:
                        continue
                    if not isinstance(record, dict):
                        continue
                    hostname = record.get("rrname", "")
                    if hostname.startswith("*."):
                        hostname = hostname[2:] # remove the "*."
                    hostname = hostname.lower()
                    if not self.plausible_hostname(hostname):
                        continue
                    if (
                        hostname.endswith("." + self.domain_root)
                        and not is_filtered(hostname, self.filter_strings)
                        and hostname not in self.results.data[self.source]["subdomains"]
                    ):
                        self.results.data[self.source]["subdomains"].add(hostname)
                        logging.info(f"{Fore.LIGHTGREEN_EX}[+] {hostname}{Style.RESET_ALL}{Fore.WHITE} [Robtex]")
        except (
            requests.exceptions.RequestException,
            NameError,
            json.decoder.JSONDecodeError,
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