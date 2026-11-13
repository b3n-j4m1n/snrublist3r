import aiodns
import asyncio
import logging
import string
import socket
import struct
import random

from pkg.utils.error_handler import ErrorHandler
from pkg.utils.filter_handler import is_filtered
from pkg.utils.output_handler import OutputHandler
from pkg.utils.results import Results

from colorama import Fore, Back, Style
from tqdm import tqdm

# c-ares error codes surfaced in aiodns.error.DNSError.args[0]
ARES_ENODATA = 1        # no answer records, NOTE: modern c-ares conflates NXDOMAIN
                        # and NODATA into this code, use raw_rcode() to tell them apart
ARES_ESERVFAIL = 3      # resolver failed to process the query, worth retrying elsewhere
ARES_ENOTFOUND = 4      # NXDOMAIN, name does not exist
ARES_ECONNREFUSED = 11  # resolver unreachable, worth retrying elsewhere
ARES_ETIMEOUT = 12      # resolver did not answer, worth retrying elsewhere
RETRYABLE_ERROR_CODES = frozenset([ARES_ESERVFAIL, ARES_ECONNREFUSED, ARES_ETIMEOUT])

# raw DNS response codes, only used for ENODATA disambiguation
RCODE_NOERROR = 0
RCODE_NXDOMAIN = 3

# random names probed during wildcard detection
WILDCARD_PROBE_COUNT = 5
WILDCARD_PROBE_LENGTH = 12


class RawDNSProtocol(asyncio.DatagramProtocol):
    # minimal UDP DNS client, only used to read the response code that c-ares
    # discards when it conflates NXDOMAIN and NODATA into ARES_ENODATA
    def __init__(self, txid, loop):
        self.txid = txid
        self.loop = loop
        self.rcode = None
        self.response_future = loop.create_future()

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        if len(data) >= 4 and struct.unpack('>H', data[:2])[0] == self.txid:
            self.rcode = data[3] & 0xF
            if not self.response_future.done():
                self.response_future.set_result(self.rcode)

    def error_received(self, exc):
        if not self.response_future.done():
            self.response_future.set_result(None)


def build_a_query(qname, txid):
    # DNS header with RD=1, one question, type A, class IN
    header = struct.pack('>HHHHHH', txid, 0x0100, 1, 0, 0, 0)
    labels = b''.join(bytes([len(part)]) + part.encode('ascii') for part in qname.rstrip('.').split('.'))
    return header + labels + b'\x00' + struct.pack('>HH', 1, 1)


class DNSBruteForce:
    def __init__(self, tasks, resolvers, operating_system, sources_name, timeout, dns_retries, verbosity_level, output_file, wildcard_evasion=False, filter_strings=None):
        self.operating_system = operating_system
        self.domains = []
        self.sources_name = sources_name
        self.results = Results(self.sources_name)
        self.resolvers = resolvers
        self.tasks = tasks
        self.timeout = timeout
        self.dns_retries = dns_retries
        # pycares hooks into the event loop with add_reader, which the Windows
        # proactor loop does not support, so a selector loop is constructed
        # explicitly on Windows instead of going through the deprecated event
        # loop policy API (set_event_loop_policy)
        self.loop = asyncio.SelectorEventLoop() if operating_system == 'nt' else asyncio.new_event_loop()
        if self.resolvers:
            self.resolver_pool = [
                aiodns.DNSResolver(nameservers=[resolver_ip], loop=self.loop, timeout=self.timeout, tries=self.dns_retries, rotate=True)
                for resolver_ip in self.resolvers
            ]
        else:
            self.resolver_pool = [aiodns.DNSResolver(loop=self.loop, timeout=self.timeout, tries=self.dns_retries, rotate=True)]
        self.resolver_index = 0
        self.wildcard_ips = set()
        # True when the resolver stack returns real ENOTFOUND codes, meaning a
        # plain ENODATA can be trusted as "name exists, no A record"
        self.enodata_is_hit = False
        # True when raw response code probing is trusted, i.e. the raw channel
        # reported NXDOMAIN for a fabricated probe name and never reported
        # NOERROR for one (some transparent DNS middleboxes NODATA-mangle every
        # negative answer, which makes raw response codes useless)
        self.use_raw_disambiguation = False
        self.task_list = []
        self.queue = None # created inside the running loop in produce()
        self.verbosity_level = verbosity_level
        self.output_file = output_file
        self.wildcard_evasion = wildcard_evasion
        self.filter_strings = filter_strings
        self.eh = ErrorHandler()

    def next_resolver_index(self):
        index = self.resolver_index
        self.resolver_index = (self.resolver_index + 1) % len(self.resolver_pool)
        return index

    async def resolve(self, domain, record="A"):
        # round-robin across the resolver channels, on a retryable failure
        # (SERVFAIL, timeout, connection refused) retry once via a different resolver,
        # returns (answers, resolver_ip) so ENODATA results can be disambiguated
        # with a raw query to the same resolver
        index = self.next_resolver_index()
        resolver_ip = self.resolvers[index] if self.resolvers else None
        try:
            answers = await self.resolver_pool[index].query(domain, record)
            return answers, resolver_ip
        except aiodns.error.DNSError as error:
            if error.args[0] in RETRYABLE_ERROR_CODES and len(self.resolver_pool) > 1:
                retry_index = (index + 1) % len(self.resolver_pool)
                resolver_ip = self.resolvers[retry_index] if self.resolvers else None
                answers = await self.resolver_pool[retry_index].query(domain, record)
                return answers, resolver_ip
            raise

    async def raw_rcode(self, qname, resolver_ip):
        # sends one raw UDP DNS query and returns the raw response code, or None
        # if the probe could not be completed
        if resolver_ip is None:
            return None
        txid = random.getrandbits(16)
        try:
            query = build_a_query(qname, txid)
        except (UnicodeEncodeError, struct.error):
            return None
        protocol = RawDNSProtocol(txid, self.loop)
        try:
            transport, _ = await asyncio.wait_for(
                self.loop.create_datagram_endpoint(lambda: protocol, remote_addr=(resolver_ip, 53)),
                timeout=self.timeout
            )
        except (OSError, asyncio.TimeoutError):
            return None
        try:
            transport.sendto(query)
            return await asyncio.wait_for(protocol.response_future, timeout=self.timeout)
        except asyncio.TimeoutError:
            return None
        finally:
            transport.close()

    @staticmethod
    def answer_ips(answers):
        # aiodns/pycares returns A record addresses as either strings or packed
        # integers depending on the version, normalize both to dotted-quad strings
        ips = set()
        for answer in answers or []:
            host = getattr(answer, 'host', None)
            if host is None:
                continue
            if isinstance(host, int):
                try:
                    host = socket.inet_ntoa(struct.pack('!I', host))
                except (struct.error, OSError):
                    host = str(host)
            ips.add(str(host))
        return ips

    async def produce(self, subdomains):
        # the queue is created inside the running loop so it binds to the
        # correct event loop on every Python version
        self.queue = asyncio.Queue()
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

    async def probe_wildcard(self, domain):
        # default mode wildcard check, a single random name resolved through
        # the configured resolvers, any answer means a wildcard is present
        probe_name = ''.join(random.choice(string.ascii_lowercase) for _ in range(WILDCARD_PROBE_LENGTH)) + '.' + domain
        try:
            await self.resolve(probe_name, 'A')
            return True
        except aiodns.error.DNSError:
            return False

    async def check_wildcard(self, domain):
        # probe random names through the configured resolvers, any answer means a
        # wildcard, the probe IPs are collected so that hits resolving only to
        # wildcard IPs can be filtered during the brute force, the error codes the
        # probes produce also reveal whether this resolver stack reports real
        # ENOTFOUND codes or conflates NXDOMAIN into ENODATA, and the raw response
        # codes for the same fabricated names reveal whether raw response code
        # probing can be trusted for ENODATA disambiguation
        probes = [''.join(random.choice(string.ascii_lowercase) for _ in range(WILDCARD_PROBE_LENGTH)) for _ in range(WILDCARD_PROBE_COUNT)]
        wildcard_ips = set()
        saw_enodata = False
        saw_enotfound = False
        raw_saw_nxdomain = False
        raw_saw_noerror = False
        for probe in probes:
            probe_name = probe + '.' + domain
            try:
                answers, _ = await self.resolve(probe_name, 'A')
                wildcard_ips.update(self.answer_ips(answers))
            except aiodns.error.DNSError as error:
                if error.args[0] == ARES_ENODATA:
                    saw_enodata = True
                    resolver_ip = self.resolvers[self.next_resolver_index()] if self.resolvers else None
                    rcode = await self.raw_rcode(probe_name, resolver_ip)
                    if rcode == RCODE_NXDOMAIN:
                        raw_saw_nxdomain = True
                    elif rcode == RCODE_NOERROR:
                        # the probe name is fabricated, NOERROR for it means the
                        # network NODATA-mangles negative answers and raw codes
                        # cannot be trusted
                        raw_saw_noerror = True
                elif error.args[0] == ARES_ENOTFOUND:
                    saw_enotfound = True
        self.enodata_is_hit = saw_enotfound and not saw_enodata
        self.use_raw_disambiguation = saw_enodata and not self.enodata_is_hit and raw_saw_nxdomain and not raw_saw_noerror
        return wildcard_ips

    async def worker(self, queue):
        try:
            while not queue.empty():
                domain = await queue.get()
                try:
                    found = False
                    ips = set()
                    try:
                        answers, resolver_ip = await self.resolve(domain, 'A')
                        ips = self.answer_ips(answers)
                        found = True
                    except aiodns.error.DNSError as error:
                        if error.args[0] == ARES_ENODATA:
                            # ENODATA for A can mean the host exists with only
                            # an AAAA record (IPv6-only), so AAAA is checked
                            # before the name is written off
                            try:
                                aaaa_answers, _ = await self.resolve(domain, 'AAAA')
                                aaaa_ips = self.answer_ips(aaaa_answers)
                                if aaaa_ips:
                                    found = True
                                    ips = aaaa_ips
                            except aiodns.error.DNSError:
                                pass
                            if not found:
                                # modern c-ares conflates NXDOMAIN and NODATA into
                                # ENODATA, when raw response code probing is trusted
                                # check the raw response code to tell a CNAME/MX/TXT/
                                # AAAA-only host (RCODE_NOERROR) apart from a
                                # non-existent host (RCODE_NXDOMAIN)
                                if self.use_raw_disambiguation:
                                    rcode = await self.raw_rcode(domain, resolver_ip)
                                    found = rcode == RCODE_NOERROR or (rcode is None and self.enodata_is_hit)
                                else:
                                    # fall back to how this resolver stack behaved
                                    # during wildcard probing
                                    found = self.enodata_is_hit
                        elif error.args[0] != ARES_ENOTFOUND:
                            if self.verbosity_level >= 3 and self.timeout_bar is not None:
                                self.timeout_bar.update()
                    if found and (not ips or not self.wildcard_ips or not ips.issubset(self.wildcard_ips)):
                        if self.verbosity_level >= 3:
                            tqdm.write('\033[92m' + "[+] " + domain + '\033[1m')
                        self.results.data[self.sources_name]["subdomains"].add(domain)
                        # keep the resolved IPs next to the hit, an empty set means
                        # the host exists but answers with no A record
                        self.results.data[self.sources_name]["ips"][domain] = ips
                finally:
                    if self.verbosity_level >= 3:
                        self.progress_bar.update()
                    queue.task_done()
        except KeyboardInterrupt as error:
            self.eh.handle_error(error, source="Brute Force")

    def run(self, domain, subdomains):
        # domains containing filter strings are never resolved
        if self.filter_strings:
            subdomains = [candidate for candidate in subdomains if not is_filtered(candidate, self.filter_strings)]
        if self.wildcard_evasion:
            # wildcard evasion, multiple random names probed through the
            # configured resolvers, their IPs collected so hits resolving
            # only to wildcard IPs can be filtered during the brute force.
            # with slow or dead resolvers this is where a longer pause
            # (probes x timeout x retries, plus raw response probes) happens
            logging.warning(f"[*] checking wildcard response for {domain}...")
            self.wildcard_ips = self.loop.run_until_complete(self.check_wildcard(domain))
            if self.wildcard_ips:
                logging.warning(f"{Fore.LIGHTYELLOW_EX}[!] wildcard subdomain detected ({len(self.wildcard_ips)} wildcard IPs), results resolving only to wildcard IPs will be filtered")
        else:
            # default mode, a single random name probe through the configured
            # resolvers, any answer means a wildcard and the brute force is
            # skipped entirely
            if self.loop.run_until_complete(self.probe_wildcard(domain)):
                logging.warning(f"{Fore.LIGHTRED_EX}[-] wildcard subdomain detected, skipping brute force")
                return self.results.data
        if self.verbosity_level >= 3:
            self.progress_bar = tqdm(desc="progress", total=len(subdomains), unit=" requests", maxinterval=0.1, mininterval=0, miniters=1, smoothing=0, colour='WHITE')
            self.timeout_bar = tqdm(desc="error", total=len(subdomains), unit=" errors", maxinterval=1, mininterval=1, colour='RED')
        else:
            self.progress_bar = None
            self.timeout_bar = None
        try:
            self.loop.run_until_complete(self.produce(subdomains))
        finally:
            if self.output_file:
                oh = OutputHandler()
                oh.handle_output(self.output_file, self.results.data)

        return self.results.data