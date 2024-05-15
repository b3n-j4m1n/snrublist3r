import logging
import socket
import ssl
import sys

from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from tqdm import tqdm

class SANSearch:
    def __init__(self, domain_root, sources_name, found_subdomains, timeout, verbosity_level, output_file):
        self.domain_root = domain_root
        self.sources_name = sources_name
        self.found_subdomains = found_subdomains
        self.timeout = timeout
        self.verbosity_level = verbosity_level
        self.output_file = output_file
        self.source = "SAN Search"
        self.results = Results(self.source)


    def run(self, port=443):
        if self.verbosity_level > 0:
            self.progress_bar = tqdm(desc="progress", total=len(self.found_subdomains), unit=" requests", maxinterval=0.1, mininterval=0, miniters=1, smoothing=0, colour='WHITE')
            self.timeout_bar = tqdm(desc="error", total=len(self.found_subdomains), unit=" errors", maxinterval=1, mininterval=1, colour='RED')
        else:
            self.progress_bar = None
            self.timeout_bar = None

        for domain in self.found_subdomains:
            try:
                context = ssl.create_default_context()
                with socket.create_connection((domain, port), timeout=self.timeout) as sock:
                    with context.wrap_socket(sock, server_hostname=domain) as ssock:
                        cert = ssock.getpeercert()
                        for entry in cert.get('subjectAltName', []):
                            domain = entry[1]
                            if sys.version_info >= (3, 9):
                                domain = domain.removeprefix("*.")
                            if (
                                domain.endswith("." + self.domain_root)
                                and domain not in self.results.data[self.sources_name]['subdomains']
                            ):
                                self.results.data[self.sources_name]['subdomains'].add(domain)
                                if self.verbosity_level > 0:
                                    tqdm.write('\033[92m' + "[+] " + domain + '\033[1m')
                self.progress_bar.update()
            except Exception as e:
                if logging.getLogger().isEnabledFor(logging.DEBUG):
                    tqdm.write('\033[91m[ERROR]\033[0m ' + domain + ': ' + str(e))
                self.timeout_bar.update()

        if self.output_file:
            oh = OutputHandler()
            oh.handle_output(self.output_file, self.results.data)

        return self.results.data