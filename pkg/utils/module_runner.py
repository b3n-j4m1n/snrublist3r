import logging
from pkg.scrape import (
    # alienvault,
    anubis,
    # ask,
    # bing,
    certificatesearch,
    chaos,
    commoncrawl,
    # digitorus,
    dnsdumpster,
    # duckduckgo,
    gist,
    # google,
    hackertarget,
    hudsonrock,
    rapiddns,
    # subdomaincenter,
    thc,
    # threatcrowd,
    virustotal,
    waybackmachine,
    yahoo,
)

from pkg.bruteforce.dnsbruteforce import DNSBruteForce
from pkg.subjectaltnames.san_search import SANSearch
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
            # "alienvault",
            "anubis",
            # "ask",
            # "bing",
            "certificatesearch",
            "chaos",
            "commoncrawl",
            # "digitorus",
            "dnsdumpster",
            # "duckduckgo",
            "gist",
            # "google",
            "hackertarget",
            "hudsonrock",
            "rapiddns",
            # "subdomaincenter",
            "thc",
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
            "chaos",
            # "digitorus",
            "dnsdumpster",
            "hackertarget",
            "hudsonrock",
            "rapiddns",
            # "subdomaincenter",
            "thc",
            # "threatcrowd",
            "virustotal",
            "yahoo"
        ]
        sources_selected = []
        sources_modules = {
            # 'alienvault': alienvault.AlienVault(domain, proxy, output_file),
            'anubis': anubis.Anubis(domain, proxy, output_file),
            # 'ask': ask.Ask(domain, proxy, output_file),
            # 'bing': bing.Bing(domain, proxy, output_file),
            'certificatesearch': certificatesearch.CertificateSearch(domain, proxy, output_file),
            'chaos': chaos.Chaos(domain, proxy, output_file),
            'commoncrawl': commoncrawl.CommonCrawl(domain, proxy, output_file),
            # 'digitorus': digitorus.Digitorus(domain, proxy, output_file),
            'dnsdumpster': dnsdumpster.DNSDumpster(domain, proxy, output_file),
            # 'duckduckgo': duckduckgo.DuckDuckGo(domain, proxy, output_file),
            'gist': gist.Gist(domain, proxy, output_file),
            # 'google': google.Google(domain, proxy, output_file),
            'hackertarget': hackertarget.HackerTarget(domain, proxy, output_file),
            'hudsonrock': hudsonrock.HudsonRock(domain, proxy, output_file),
            'rapiddns': rapiddns.RapidDNS(domain, proxy, output_file),
            # 'subdomaincenter': subdomaincenter.SubdomainCenter(domain, proxy, output_file),
            'thc': thc.THC(domain, proxy, output_file),
            # 'threatcrowd': threatcrowd.ThreatCrowd(domain, proxy, output_file),
            'virustotal': virustotal.VirusTotal(domain, proxy, output_file),
            'waybackmachine': waybackmachine.WaybackMachine(domain, proxy, output_file),
            'yahoo': yahoo.Yahoo(domain, proxy, output_file),
        }
        sources_names = {
            # 'alienvault': "AlienVault",
            'anubis': "Anubis",
            # 'ask': "Ask",
            # 'bing': "Bing",
            'certificatesearch': "Certificate Search",
            'chaos': "Chaos",
            'commoncrawl': "Common Crawl",
            # 'digitorus': "Digitorus",
            # 'duckduckgo': "DuckDuckGo",
            'dnsdumpster': "DNSDumpster",
            'gist': "Gist",
            # 'google': "Google",
            'hackertarget': "Hacker Target",
            'hudsonrock': "Hudson Rock",
            'rapiddns': "RapidDNS",
            # 'subdomaincenter': "Subdomain Center",
            'thc': "THC",
            # 'threatcrowd': "ThreatCrowd",
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
        logging.warning(f"[*] starting source scraper for sources {sources_selected}")
        # running selected source modules and updating the results
        for source in sources:
            results.update(sources_modules[source].run())
        return results
        
    def run_brute_force(self, domain, tasks, subdomains, resolvers, operating_system, timeout, dns_retries, verbosity_level, output_file=None):
        logging.warning(f"[*] starting raw brute force...")
        sources_name = "DNS Brute Force"
        dnsbf = DNSBruteForce(tasks, resolvers, operating_system, sources_name, timeout, dns_retries, verbosity_level, output_file)
        results = dnsbf.run(domain, subdomains)   
        return results
    
    def run_san_search(self, domain, found_subdomains, timeout, verbosity_level, output_file=None):
        logging.warning(f"[*] starting SAN search...")
        sources_name = "SAN Search"
        ssearch = SANSearch(domain, sources_name, found_subdomains, timeout, verbosity_level, output_file)
        results = ssearch.run()
        return results
    
    def run_altdns(self, domain, found_subdomains, tasks, resolvers, permutations, operating_system, max_alts, autopilot, timeout, dns_retries, verbosity_level, output_file=None):
        max_alts = int(max_alts) // 1425 # permutations is roughly 1,145 x found subdomains
        if len(found_subdomains) > max_alts:
            logging.warning(f"{Fore.LIGHTRED_EX}[-] mutation brute force cancelled, excessive permutations, use --max-alts to override")
            return set()
        logging.warning(f"[*] mutating known subdomains")
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
                logging.warning(f"[*] mutation brute force cancelled")
                return set()
            elif altdns_length_prompt != ("y"):
                logging.debug(f"{Fore.LIGHTRED_EX}[-] invalid response")
                return set()
            else:
                logging.warning(f"[*] starting mutation brute force...")
                pass
        dnsbf = DNSBruteForce(tasks, resolvers, operating_system, sources_name, timeout, dns_retries, verbosity_level, output_file)
        results = dnsbf.run(domain, permutations)
        return results
