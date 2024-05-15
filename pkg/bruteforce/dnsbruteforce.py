import aiodns
import asyncio
import logging
import string
import socket
import random

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Back, Style
from tqdm import tqdm


class DNSBruteForce:
    def __init__(self, tasks, nameservers, operating_system, sources_name, timeout, dns_retries, verbosity_level, output_file):
        self.operating_system = operating_system
        if operating_system == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        self.domains = []
        self.sources_name = sources_name
        self.results = Results(self.sources_name)
        self.nameservers = nameservers
        self.tasks = tasks
        self.timeout = timeout
        self.dns_retries = dns_retries
        self.resolver = aiodns.DNSResolver(nameservers=self.nameservers , timeout=self.timeout, tries=self.dns_retries, rotate=True)
        self.task_list = []
        self.queue = asyncio.Queue()
        self.verbosity_level = verbosity_level
        self.output_file = output_file
        self.eh = ErrorHandler()

    async def produce(self, subdomains):
        for domain in subdomains:
            self.queue.put_nowait(domain)
        for _ in range(self.tasks):
            task = asyncio.create_task(self.worker(self.queue))
            self.task_list.append(task)
        await self.queue.join()
        for task in self.task_list:
            task.cancel()
        await asyncio.gather(*self.task_list, return_exceptions=True)
        return self.results.data

    async def worker(self, queue):
        try:
            while not queue.empty():
                domain = await queue.get()
                try:
                    await self.resolver.query(domain, "A")
                    if self.verbosity_level > 0:
                        tqdm.write('\033[92m' + "[+] " + domain + '\033[1m')
                    self.results.data[self.sources_name]["subdomains"].add(domain)
                except aiodns.error.DNSError as error:
                    if error.args[0] != 1 and error.args[0] != 4:
                        self.timeout_bar.update()
                finally:
                    if self.verbosity_level > 0:
                        self.progress_bar.update()
                    queue.task_done()
        except KeyboardInterrupt as error:
            self.eh.handle_error(error, source="Brute Force")

    def run(self, domain, subdomains):
        letters = string.ascii_lowercase
        random_sub = ''.join(random.choice(letters) for _ in range(10))
        try:
            socket.gethostbyname(random_sub + "." + domain)
            logging.error(f"{Fore.LIGHTRED_EX}[-] wildcard subdomain detected, skipping brute force")
            return self.results.data
        except:
            pass

        if self.verbosity_level > 0:
            self.progress_bar = tqdm(desc="progress", total=len(subdomains), unit=" requests", maxinterval=0.1, mininterval=0, miniters=1, smoothing=0, colour='WHITE')
            self.timeout_bar = tqdm(desc="error", total=len(subdomains), unit=" errors", maxinterval=1, mininterval=1, colour='RED')
        else:
            self.progress_bar = None
            self.timeout_bar = None
        self.resolver.loop.run_until_complete(self.produce(subdomains))

        if self.output_file:
            oh = OutputHandler()
            oh.handle_output(self.output_file, self.results.data)

        return self.results.data