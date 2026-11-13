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
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            ip_lines = []
            for source, data in self.results.items():
                for subdomain, ips in sorted(data.get("ips", {}).items()):
                    ip_list = ', '.join(sorted(ips)) if ips else 'no A record'
                    ip_lines.append(f"[*] {subdomain}: {Fore.LIGHTCYAN_EX}{ip_list}{Style.RESET_ALL}")
            if ip_lines:
                logging.debug('\n'.join(ip_lines))
        logging.warning(f"[*] results per source:")
        for source, data in self.results.items():
            subdomain_count = len(data["subdomains"])
            truncated_suffix = " (truncated)" if data.get("truncated") else ""
            elapsed_suffix = f" ({data['elapsed']}s)" if "elapsed" in data else ""
            logging.warning(f"[*] {source}: {Fore.LIGHTGREEN_EX}{subdomain_count}{Style.RESET_ALL}{truncated_suffix}{elapsed_suffix}")

    def print_finished(self):
        unique_subdomains = set()
        for key, value in self.results.items():
            unique_subdomains.update(value['subdomains'])
        logging.warning(f"FINISHED! {Fore.LIGHTGREEN_EX}{len(unique_subdomains)}{Style.RESET_ALL} unique subdomains snrubed in {round((time.time() - self.start_time), 2)} seconds")