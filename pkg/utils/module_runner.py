import logging
from pkg.scrape import (
    alienvault,
    anubis,
    ask,
    bing,
    certificatesearch,
    digitorus,
    dnsdumpster,
    duckduckgo,
    gist,
    google,
    hackertarget,
    rapiddns,
    virustotal,
    waybackmachine,
    yahoo,
)

from pkg.bruteforce.dnsbruteforce import DNSBruteForce
from pkg.bruteforce.altdns import AltDNS

import colorama
from colorama import Fore, Back, Style

class ModuleRunner:
    def __init__(self):
        colorama.init(autoreset=True)

    def run_scraper(self, domain, proxy, sources=None, fast=False, output_file=None):
        results = {}
        if sources and fast:
            raise ValueError(f"{Fore.LIGHTRED_EX}[-] cannot have both -s/--sources and --fast arguments")
        if not sources and not fast:
            sources = [
            "alienvault",
            "anubis",
            "ask",
            "bing",
            "certificatesearch",
            "digitorus",
            "dnsdumpster",
            "duckduckgo",
            "gist",
            "google",
            "hackertarget",
            "rapiddns",
            "virustotal",
            "waybackmachine",
            "yahoo"
        ]
        elif sources and not fast:
            sources = sources.split(',')
        elif fast and not sources:
            sources = [
            "alienvault",
            "anubis",
            "ask",
            "bing",
            "certificatesearch",
            "digitorus",
            "dnsdumpster",
            "hackertarget",
            "rapiddns",
            "virustotal",
            "waybackmachine",
            "yahoo"
        ]
        sources_selected = []
        sources_modules = {
            'alienvault': alienvault.AlienVault(domain, proxy, output_file),
            'anubis': anubis.Anubis(domain, proxy, output_file),
            'ask': ask.Ask(domain, proxy, output_file),
            'bing': bing.Bing(domain, proxy, output_file),
            'certificatesearch': certificatesearch.CertificateSearch(domain, proxy, output_file),
            'digitorus': digitorus.Digitorus(domain, proxy, output_file),
            'dnsdumpster': dnsdumpster.DNSDumpster(domain, proxy, output_file),
            'duckduckgo': duckduckgo.DuckDuckGo(domain, proxy, output_file),
            'gist': gist.Gist(domain, proxy, output_file),
            'google': google.Google(domain, proxy, output_file),
            'hackertarget': hackertarget.HackerTarget(domain, proxy, output_file),
            'rapiddns': rapiddns.RapidDNS(domain, proxy, output_file),
            'virustotal': virustotal.VirusTotal(domain, proxy, output_file),
            'waybackmachine': waybackmachine.WaybackMachine(domain, proxy, output_file),
            'yahoo': yahoo.Yahoo(domain, proxy, output_file),
        }
        sources_names = {
            'alienvault': "AlienVault",
            'anubis': "Anubis",
            'ask': "Ask",
            'bing': "Bing",
            'certificatesearch': "Certificate Search",
            'digitorus': "Digitorus",
            'duckduckgo': "DuckDuckGo",
            'dnsdumpster': "DNSDumpster",
            'gist': "Gist",
            'google': "Google",
            'hackertarget': "Hacker Target",
            'rapiddns': "RapidDNS",
            'virustotal': "VirusTotal",
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
        logging.warn(f"[*] starting source scraper for sources {sources_selected}")
        # running selected source modules and updating the results
        for source in sources:
            results.update(sources_modules[source].run())
        return results
        
    
    def run_brute_force(self, domain, tasks, subdomains, nameservers, operating_system, timeout, dns_retries, verbosity_level, output_file=None):
        logging.warning(f"[*] starting raw brute force...")
        sources_name = "DNS Brute Force"
        dnsbf = DNSBruteForce(tasks, nameservers, operating_system, sources_name, timeout, dns_retries, verbosity_level, output_file)
        results = dnsbf.run(domain, subdomains)   
        return results
    
    def run_altdns(self, domain, found_subdomains, tasks, nameservers, permutations, operating_system, max_alts, autopilot, timeout, dns_retries, verbosity_level, output_file=None):
        max_alts = int(max_alts) // 1425
        if len(found_subdomains) > max_alts:
            logging.error(f"{Fore.LIGHTRED_EX}[-] mutation brute force cancelled, excessive permutations, use --max-alts to override")
            return set()
        logging.warn(f"[*] mutating known subdomains")
        sources_name = "AltDNS"
        adns = AltDNS(found_subdomains, permutations)
        permutations = set().union(
            adns.insert_all_indexes(),
            adns.insert_number_suffix_subdomains(),
            adns.insert_dash_subdomains(),
            adns.join_words_subdomains()
            )
        permutations = {item for item in permutations if item.endswith('.' + domain)} # this removes improperly mutated results if the root domain is a nested domain, e.g. test.example.com, mutations such as test.api.example.com (api and test swapped, does not end with 'test.example.com') will be removed
        logging.warning(f"[*] {len(permutations)} subdomain mutations generated")
        if autopilot is True:
            pass
        else:
            print(Fore.LIGHTYELLOW_EX + "[?] continue with mutation brute force (y/n)? ", end='') # input() doesn't work with colorama
            altdns_length_prompt = input()
            if altdns_length_prompt == ("n"):
                logging.warn(f"[*] mutation brute force cancelled")
                return set()
            elif altdns_length_prompt != ("y"):
                logging.error(f"{Fore.LIGHTRED_EX}[-] invalid response")
                return set()
            else:
                logging.warn(f"[*] starting mutation brute force...")
                pass
        dnsbf = DNSBruteForce(tasks, nameservers, operating_system, sources_name, timeout, dns_retries, verbosity_level, output_file)
        results = dnsbf.run(domain, permutations)
        return results
