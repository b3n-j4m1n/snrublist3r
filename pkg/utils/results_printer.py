import logging
import time

from colorama import Fore, Back, Style

class ResultsPrinter:
    def __init__(self, start_time, results):
        self.start_time = start_time
        self.results = results

    def print_summary(self):
        results_set = set(subdomain for key in self.results.keys() for subdomain in self.results[key]['subdomains'])
        logging.warning('\n'.join(results_set))

        for source, data in self.results.items():
            subdomain_count = len(data["subdomains"])
            if 'DNS Brute Force' not in source and 'AltDNS' not in source:
                scrape_summary = f"[*] {source}: {Fore.LIGHTGREEN_EX}{subdomain_count}{Style.RESET_ALL}"
                logging.warning(scrape_summary)
            if 'DNS Brute Force' in source or 'AltDNS' in source:
                brute_force_summary = f"[*] {source}: {Fore.LIGHTGREEN_EX}{subdomain_count}{Style.RESET_ALL}"
                logging.warning(brute_force_summary)

    def print_finished(self):
        unique_subdomains = set()
        for key, value in self.results.items():
            unique_subdomains.update(value['subdomains'])
        logging.warning(f"FINISHED! {Fore.LIGHTGREEN_EX}{len(unique_subdomains)}{Style.RESET_ALL} unique subdomains snrubed in {round((time.time() - self.start_time), 2)} seconds")