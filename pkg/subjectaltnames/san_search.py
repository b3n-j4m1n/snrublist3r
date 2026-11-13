import logging
import socket
import ssl
import sys
from concurrent.futures import ThreadPoolExecutor

from pkg.utils.filter_handler import is_filtered
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from tqdm import tqdm

class SANSearch:
    PORTS = (443, 8443, 993, 465, 587) # ports checked for certificates

    def __init__(self, domain_root, sources_name, found_subdomains, timeout, verbosity_level, output_file, tasks=256, filter_strings=None):
        self.domain_root = domain_root
        self.sources_name = sources_name
        self.found_subdomains = found_subdomains
        self.timeout = timeout
        self.verbosity_level = verbosity_level
        self.output_file = output_file
        self.tasks = max(1, int(tasks))
        self.filter_strings = filter_strings
        self.source = "SAN Search"
        self.results = Results(self.source)

    def check_host(self, domain, port):
        # returns (found_names, errored), found_names contains the names harvested
        # from the host certificate's Subject Alt Names and Subject Common Name
        found = set()
        errored = False
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    names = set()
                    for entry in cert.get('subjectAltName', []) or []:
                        if entry[0].lower() == 'dns':
                            names.add(entry[1])
                    for rdn in cert.get('subject', ()) or ():
                        for key, value in rdn:
                            if key.lower() == 'commonname':
                                names.add(value)
                    for name in names:
                        if sys.version_info >= (3, 9):
                            name = name.removeprefix("*.")
                        elif name.startswith("*."):
                            name = name[2:]
                        if name.endswith("." + self.domain_root):
                            found.add(name)
        except Exception as e:
            errored = True
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                tqdm.write('\033[91m[ERROR]\033[0m ' + domain + ': ' + str(e))
        return found, errored

    def run(self, port=None):
        ports = (port,) if port is not None else self.PORTS
        hosts = sorted(host for host in self.found_subdomains if not is_filtered(host, self.filter_strings))
        if self.verbosity_level >= 3:
            self.progress_bar = tqdm(desc="progress", total=len(hosts) * len(ports), unit=" requests", maxinterval=0.1, mininterval=0, miniters=1, smoothing=0, colour='WHITE')
            self.timeout_bar = tqdm(desc="error", total=len(hosts) * len(ports), unit=" errors", maxinterval=1, mininterval=1, colour='RED')
        else:
            self.progress_bar = None
            self.timeout_bar = None

        # hosts are checked concurrently against every port, results are
        # collected in submission order
        with ThreadPoolExecutor(max_workers=self.tasks) as executor:
            for port_number in ports:
                for host, (found_names, errored) in zip(hosts, executor.map(lambda host: self.check_host(host, port_number), hosts)):
                    for name in found_names:
                        if (
                            name not in self.results.data[self.source]['subdomains']
                            and not is_filtered(name, self.filter_strings)
                        ):
                            self.results.data[self.source]['subdomains'].add(name)
                            if self.verbosity_level >= 3:
                                tqdm.write('\033[92m' + "[+] " + name + '\033[1m')
                    if self.verbosity_level >= 3:
                        self.progress_bar.update()
                        if errored:
                            self.timeout_bar.update()

        if self.output_file:
            oh = OutputHandler()
            oh.handle_output(self.output_file, self.results.data)

        return self.results.data