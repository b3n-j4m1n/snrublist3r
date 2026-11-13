import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pkg.scrape import (
            # alienvault,
    anubis,
    # ask,
    # bing,
    certificatesearch,
    certspotter,
    chaos,
    commoncrawl,
            # digitorus,
    dnsdumpster,
    dnsrepo,
    # duckduckgo,
    gist,
    # google,
    hackertarget,
    hudsonrock,
    netlas,
    rapiddns,
    robtex,
    subdomaincenter,
    thc,
    urlscan,
    # threatcrowd,
    virustotal,
    waybackmachine,
    yahoo,
)

from pkg.bruteforce.dnsbruteforce import DNSBruteForce
from pkg.subjectaltnames.san_search import SANSearch
from pkg.bruteforce.altdns import AltDNS
from pkg.utils.results import Results
from pkg.utils.filter_handler import is_filtered

import colorama
from colorama import Fore, Back, Style

class ModuleRunner:
    def __init__(self):
        colorama.init(autoreset=True)

    def run_scraper(self, domain, proxy, sources=None, fast=False, output_file=None, filter_strings=None):
        results = {}
        if sources and fast:
            raise ValueError(f"{Fore.LIGHTRED_EX}[-] cannot have both -s/--sources and --fast arguments")
        if not sources and not fast:
            sources = [
            # "alienvault",
            "anubis",
            # "ask",
            # "bing",
            "certificatesearch",
            "certspotter",
            "chaos",
            "commoncrawl",
            # "digitorus",
            "dnsdumpster",
            "dnsrepo",
            # "duckduckgo",
            "gist",
            # "google",
            "hackertarget",
            "hudsonrock",
            "netlas",
            "rapiddns",
            "robtex",
            "subdomaincenter",
            "thc",
            "urlscan",
            # "threatcrowd",
            "virustotal",
            "waybackmachine",
            "yahoo"
        ]
        elif sources and not fast:
            sources = sources.split(',')
        elif fast and not sources:
            sources = [
            # "alienvault",
            "anubis",
            # "ask",
            # "bing",
            "certificatesearch",
            "certspotter",
            "dnsrepo",
            "netlas",
            "chaos",
            # "digitorus",
            "dnsdumpster",
            # "duckduckgo",
            # "gist",
            # "google",
            "hackertarget",
            "hudsonrock",
            "rapiddns",
            "subdomaincenter",
            "thc",
            "urlscan",
            # "threatcrowd",
            "virustotal",
            "yahoo"
        ]
        sources_selected = []
        sources_modules = {
            # 'alienvault': "AlienVault",
            'anubis': anubis.Anubis(domain, proxy, output_file, filter_strings),
            # 'ask': ask.Ask(domain, proxy, output_file, filter_strings),
            # 'bing': bing.Bing(domain, proxy, output_file, filter_strings),
            'certificatesearch': certificatesearch.CertificateSearch(domain, proxy, output_file, filter_strings),
            'certspotter': certspotter.CertSpotter(domain, proxy, output_file, filter_strings),
            'chaos': chaos.Chaos(domain, proxy, output_file, filter_strings),
            'commoncrawl': commoncrawl.CommonCrawl(domain, proxy, output_file, filter_strings),
            # 'digitorus': "Digitorus",
            'dnsdumpster': dnsdumpster.DNSDumpster(domain, proxy, output_file, filter_strings),
            'dnsrepo': dnsrepo.DNSRepo(domain, proxy, output_file, filter_strings),
            # 'duckduckgo': duckduckgo.DuckDuckGo(domain, proxy, output_file, filter_strings),
            'gist': gist.Gist(domain, proxy, output_file, filter_strings),
            # 'google': google.Google(domain, proxy, output_file, filter_strings),
            'hackertarget': hackertarget.HackerTarget(domain, proxy, output_file, filter_strings),
            'hudsonrock': hudsonrock.HudsonRock(domain, proxy, output_file, filter_strings),
            'netlas': netlas.Netlas(domain, proxy, output_file, filter_strings),
            'rapiddns': rapiddns.RapidDNS(domain, proxy, output_file, filter_strings),
            'robtex': robtex.Robtex(domain, proxy, output_file, filter_strings),
            'subdomaincenter': subdomaincenter.SubdomainCenter(domain, proxy, output_file, filter_strings),
            'thc': thc.THC(domain, proxy, output_file, filter_strings),
            'urlscan': urlscan.URLScan(domain, proxy, output_file, filter_strings),
            # 'threatcrowd': threatcrowd.ThreatCrowd(domain, proxy, output_file, filter_strings),
            'virustotal': virustotal.VirusTotal(domain, proxy, output_file, filter_strings),
            'waybackmachine': waybackmachine.WaybackMachine(domain, proxy, output_file, filter_strings),
            'yahoo': yahoo.Yahoo(domain, proxy, output_file, filter_strings),
        }
        sources_names = {
            # 'alienvault': "AlienVault",
            'anubis': "Anubis",
            # 'ask': "Ask",
            # 'bing': "Bing",
            'certificatesearch': "Certificate Search",
            'certspotter': "Cert Spotter",
            'chaos': "Chaos",
            'commoncrawl': "Common Crawl",
            # 'digitorus': "Digitorus",
            # 'duckduckgo': "DuckDuckGo",
            'dnsdumpster': "DNSDumpster",
            'dnsrepo': "NOC DNS Database Repository Search",
            # 'google': "Google",
            'gist': "Gist",
            'hackertarget': "Hacker Target",
            'hudsonrock': "Hudson Rock",
            'netlas': "Netlas",
            'rapiddns': "RapidDNS",
            'robtex': "Robtex",
            'subdomaincenter': "Subdomain Center",
            'thc': "THC",
            'urlscan': "URLScan",
            # 'threatcrowd': "ThreatCrowd",
            'virustotal': "Virus Total",
            'waybackmachine': "Wayback Machine",
            'yahoo': "Yahoo"
        }
        # checking if arg -s values are valid sources
        for source in sources:
            if source not in sources_modules:
                raise ValueError(f"{Fore.LIGHTRED_EX}[-] unknown source {source}")
        # creating a list of source modules to run
        for source in sources:
            sources_selected.append(sources_names[source])
        logging.warning(f"[*] starting source scraper for sources {sources_selected}")
        # running selected source modules concurrently and updating the results
        with ThreadPoolExecutor(max_workers=max(1, len(sources))) as executor:
            futures = {source: executor.submit(self.timed_run, sources_modules[source]) for source in sources}
            for source, future in futures.items():
                try:
                    data, elapsed = future.result()
                    for key in data:
                        data[key]["elapsed"] = round(elapsed, 1)
                    results.update(data)
                except Exception as e:
                    logging.warning(f"{Fore.LIGHTRED_EX}[-] {sources_names.get(source, source)} scraper failed: {e}")
        return results

    @staticmethod
    def timed_run(module):
        start_time = time.time()
        data = module.run()
        return data, time.time() - start_time
        
    def run_brute_force(self, domain, tasks, subdomains, resolvers, operating_system, timeout, dns_retries, verbosity_level, output_file=None, wildcard_evasion=False, filter_strings=None):
        logging.warning(f"[*] starting raw brute force...")
        sources_name = "DNS Brute Force"
        dnsbf = DNSBruteForce(tasks, resolvers, operating_system, sources_name, timeout, dns_retries, verbosity_level, output_file, wildcard_evasion, filter_strings)
        start_time = time.time()
        results = dnsbf.run(domain, subdomains)   
        results[sources_name]["elapsed"] = round(time.time() - start_time, 1)
        return results
    
    def run_san_search(self, domain, found_subdomains, timeout, verbosity_level, output_file=None, tasks=256, filter_strings=None):
        logging.warning(f"[*] starting SAN search...")
        sources_name = "SAN Search"
        ssearch = SANSearch(domain, sources_name, found_subdomains, timeout, verbosity_level, output_file, tasks=tasks, filter_strings=filter_strings)
        start_time = time.time()
        results = ssearch.run()
        results[sources_name]["elapsed"] = round(time.time() - start_time, 1)
        return results
    
    def run_altdns(self, domain, found_subdomains, tasks, resolvers, permutations, operating_system, max_alts, autopilot, timeout, dns_retries, verbosity_level, output_file=None, wildcard_evasion=False, filter_strings=None):
        max_alts = int(max_alts)
        logging.warning(f"[*] mutating known subdomains")
        sources_name = "AltDNS"
        adaptive_words = AltDNS.harvest_adaptive_words(found_subdomains, permutations)
        if adaptive_words:
            logging.warning(f"[*] {len(adaptive_words)} adaptive permutation words harvested from found subdomains")
            permutations = permutations + adaptive_words
        adns = AltDNS(found_subdomains, permutations, max_mutations=max_alts)
        permutations = set().union(
            adns.insert_all_indexes(),
            adns.insert_number_suffix_subdomains(),
            adns.increment_number_suffix_subdomains(),
            adns.replace_component_subdomains(),
            adns.insert_dash_subdomains(),
            adns.join_words_subdomains(),
            adns.merge_adjacent_subdomains()
            )
        permutations = {item for item in permutations if item.endswith('.' + domain)} # this removes improperly mutated results if the root domain is a nested domain, e.g. test.example.com, mutations such as test.api.example.com (api and test swapped, does not end with 'test.example.com') will be removed
        permutations = {item for item in permutations if not is_filtered(item, filter_strings)} # mutations containing filter strings are never resolved
        permutations -= found_subdomains # skip subdomains that have already been confirmed live
        if adns.cap_hit:
            logging.warning(f"{Fore.LIGHTYELLOW_EX}[!] mutation generation stopped early at the --max-alts cap ({max_alts}), later found subdomains were not mutated")
        was_truncated = len(permutations) > max_alts
        if was_truncated:
            logging.warning(f"{Fore.LIGHTYELLOW_EX}[!] {len(permutations)} mutations exceed --max-alts ({max_alts}), truncating")
            permutations = set(sorted(permutations)[:max_alts])
        logging.warning(f"[*] {len(permutations)} subdomain mutations generated")
        if autopilot is True:
            pass
        else:
            print(Fore.LIGHTYELLOW_EX + "[?] continue with mutation brute force (y/n)? ", end='') # input() doesn't work with colorama
            altdns_length_prompt = input()
            if altdns_length_prompt == ("n"):
                logging.warning(f"[*] mutation brute force cancelled")
                return set()
            elif altdns_length_prompt != ("y"):
                logging.debug(f"{Fore.LIGHTRED_EX}[-] invalid response")
                return set()
            else:
                logging.warning(f"[*] starting mutation brute force...")
                pass
        dnsbf = DNSBruteForce(tasks, resolvers, operating_system, sources_name, timeout, dns_retries, verbosity_level, output_file, wildcard_evasion, filter_strings)
        start_time = time.time()
        results = dnsbf.run(domain, permutations)
        results[sources_name]["elapsed"] = round(time.time() - start_time, 1)
        results[sources_name]["truncated"] = was_truncated # shown as (truncated) in the results summary
        return results

    def run_recursive_brute_force(self, domain, found_subdomains, tasks, resolvers, operating_system, timeout, dns_retries, verbosity_level, words_file, depth=1, output_file=None, wildcard_evasion=False, filter_strings=None):
        logging.warning(f"[*] starting recursive brute force...")
        start_time = time.time()
        words = []
        with open(words_file) as file:
            for line in file:
                cleaned_line = line.strip()
                if cleaned_line and not cleaned_line.startswith('#'):
                    words.append(cleaned_line)
        depth = max(1, int(depth))
        sources_name = "Recursive Brute Force"
        results = Results(sources_name).data
        resolved = set(found_subdomains) # subdomains already confirmed live, skipped in every level
        frontier = set(found_subdomains)
        for level in range(1, depth + 1):
            if not frontier:
                break
            candidates = set()
            for parent in frontier:
                for word in words:
                    candidates.add(word + '.' + parent)
            candidates -= resolved
            candidates = {candidate for candidate in candidates if not is_filtered(candidate, filter_strings)} # candidates containing filter strings are never resolved
            if not candidates:
                break
            logging.warning(f"[*] recursion level {level}: resolving {len(candidates)} candidates")
            dnsbf = DNSBruteForce(tasks, resolvers, operating_system, sources_name, timeout, dns_retries, verbosity_level, output_file, wildcard_evasion, filter_strings)
            level_results = dnsbf.run(domain, list(candidates))
            results[sources_name]['subdomains'].update(level_results[sources_name]['subdomains'])
            results[sources_name]['ips'].update(level_results[sources_name]['ips'])
            frontier = level_results[sources_name]['subdomains'] - resolved
            resolved |= frontier
        results[sources_name]["elapsed"] = round(time.time() - start_time, 1)
        return results
