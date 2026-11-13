import argparse
import logging
import os
import signal
import sys
import time

from pkg.utils.file_handler import FileHandler
from pkg.utils.filter_handler import parse_filter_strings
from pkg.utils.results_printer import ResultsPrinter
from pkg.utils.module_runner import ModuleRunner
from pkg.utils.verbosity import Verbosity

import colorama
from colorama import Fore, Back, Style
colorama.init(autoreset=True)


def banner():
    logging.warning("""
                ⠀⠀⡠⠐⠀⠈⠁⠐⠪⢟⢁⡰⢄⠀⠀⠀⠀⠀⠀
                ⢠⠺⠀⠀⠀⠀⠀⠠⠆⡀⢣⢀⡀⢡⠀⠀⠀⠀⠀
                ⡆⡇⠀⠀⠀⠀⠀⠰⠀⡡⢳⣄⡈⡾⠀⠀⠀⠀⠀
                ⠰⡡⡀⠀⠀⠀⢀⡠⠀⢇⠻⣺⡝⠁⠀⠀⠀⠀⠀
                ⠀⢭⡩⠃⠯⣉⠡⠃⠀⠈⠊⡙⠀⠀⠀⠀⠀⠀⠀
                ⢀⠜⠤⡄⠀⠀⠀⠀⢀⣤⠌⢣⡀⣀⠀⠀⠀⠀⠀
                ⣎⡠⢺⣁⣀⣠⡴⣾⡛⠁⠀⠀⠹⢣⠹⡢⡀⠀⠀
                ⠈⠀⠀⠀⠀⠀⠀⠀⢨⢶⢤⢀⠔⢸⡇⢣⠱⡀⠀
                ⠀⠀⠀⠀⠀⠀⠀⠀⣼⢼⠾⣴⠧⡚⢴⠋⠀⠱⠀
                ⠀⠀⠀⠀⠀⠀⠀⢀⢿⡀⣇⠹⢀⠛⣸⢡⠀⠀⡇
                ⠀⠀⠀⠀⡨⢷⡺⠷⣬⢱⢻⠀⠏⡰⠃⢸⠀⠀⠀
                ⠀⠀⠀⢘⠤⢭⡿⡻⠆⠈⣷⣾⣔⣁⣀⡼⠀⠀⡄
                ⠀⠀⠀⠈⠢⡁⢸⢩⣷⣀⡸⠀⡇⠀⠀⠀⠀⣠⡇
snrublist3r            ⠉⠉⠁⠘⠛⠛⠛⠛⠚⠛⠛⠒⠃      
    """)


def parse_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    target = parser.add_argument_group('TARGET(S)')
    scraping = parser.add_argument_group('SCRAPING')
    brute_force = parser.add_argument_group('BRUTE FORCE')
    san_search = parser.add_argument_group('SAN SEARCH')
    filtering = parser.add_argument_group('FILTERING')
    configurations = parser.add_argument_group('CONFIGURATIONS')
    output = parser.add_argument_group('OUTPUT')
    verbosity = parser.add_argument_group('VERBOSITY')
	
    target.add_argument("-d", "--domain", dest="domain", help="root domain", default=None)
    target.add_argument("-df", "--domains-file", dest="domains_file", help="input file of line-separated root domains", default=None)
	
    scraping.add_argument("-s", "--sources", dest="sources", type=str, help="comma-separated list of sources, options are anubis, certificatesearch, certspotter, chaos, commoncrawl, dnsdumpster, dnsrepo, gist, hackertarget, hudsonrock, netlas, rapiddns, robtex, subdomaincenter, thc, urlscan, virustotal, waybackmachine, yahoo (default is all)")
    scraping.add_argument("--fast", dest="fast", help="run only fast scraping modules (excludes Common Crawl, Gist, Robtex, Wayback Machine)", action="store_true")
    scraping.add_argument("--proxy", dest="proxy", help="proxy used for source scraper, e.g. 'http://127.0.0.1:8080'", default=None)
    scraping.add_argument("--disable-scraping", dest="disable_scraping", help="disable scraping of any sources (use with brute force options)", action="store_true")
	
    brute_force.add_argument("-b", "--brute-force", dest="brute_force", help="enable raw brute force", action="store_true")
    brute_force.add_argument("-sf", "--subdomains-file", dest="subdomains_file", help="input file of line-separated subdomains used in the DNS brute force (default is combined_subdomains.txt)", default="./lists/combined_subdomains.txt")
    brute_force.add_argument("-rf", "--resolvers-file", dest="resolvers_file", help="input file of line-separated resolver IPs used in the DNS brute force")
    brute_force.add_argument("--tasks", dest="tasks", help="number of concurrent tasks in the brute-force and SAN-search queues (default is 256)", type=int, default=256)
    brute_force.add_argument("--timeout", dest="timeout", help="timeout on DNS resolution and SAN search (default is 3)", type=float, default=3)
    brute_force.add_argument("--dns-retries", dest="dns_retries", help="retries for DNS resolution (default is 1)", type=int, default=1)
    brute_force.add_argument("-we", "--wildcard-evasion", dest="wildcard_evasion", help="raw and mutation brute force domains resolving to wildcard domain IPs will be filtered", action="store_true")
    brute_force.add_argument("-m", "--mutation", dest="mutation", help="enable mutation brute force", action="store_true")
    brute_force.add_argument("-pf", "--permutation-file", dest="permutation_file", help="input file of line-separated strings used in the mutation DNS brute force (default is permutation-strings.txt)", default="./lists/permutation-strings.txt")
    brute_force.add_argument("-ap", "--autopilot", dest="autopilot", help="ignore input() prompts", action="store_true")
    brute_force.add_argument("-ma", "--max-alts", dest="max_alts", help="mutation resolution cap (generated mutations exceeding this are truncated), default is 1,000,000", default=1000000)
    brute_force.add_argument("-r", "--recursive", dest="recursive", help="enable recursive brute force", action="store_true")
    brute_force.add_argument("-rd", "--recursive-depth", dest="recursive_depth", help="recursion depth for the recursive brute force (default is 1)", type=int, default=1)
    brute_force.add_argument("--recursive-file", dest="recursive_file", help="input file of line-separated words used under discovered subdomains in the recursive brute force (default is subdomains-top500.txt)", default="./lists/subdomains-top500.txt")

    san_search.add_argument("--san", dest="san", help="enable Subject Alt Names search", action="store_true")

    filtering.add_argument("-fs", "--filter-string", dest="filter_string", help="case-insensitive string(s), domains containing them are excluded from processing and results, can be used multiple times and/or comma-separated (e.g. -fs \".crm.\" -fs \".foo.\")", action="append", default=None)
    
    configurations.add_argument("--loop", dest="loop", help="run in a continuous loop", action="store_true")

    output.add_argument("-o", "--output", dest="output_file", help="output file to save results", default=None)
    
    verbosity.add_argument("-v", dest="verbosity", action="count", help="enable verbosity", default=None)
    verbosity.add_argument("--debug", dest="debug", action="count", help="enable debug log level", default=None)
    verbosity.add_argument("--silent", dest="silent", action="count", help="disable terminal output", default=None)
    
    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])

    return args


def main(args):
    v = Verbosity()
    verbosity_level = v.level(verbose=args.verbosity, debug=args.debug, silent=args.silent)

    banner()

    filter_strings = parse_filter_strings(args.filter_string)
    if filter_strings:
        quoted = ', '.join(['"' + filter_string + '"' for filter_string in filter_strings])
        logging.warning(f"[*] filtering domains containing {Fore.LIGHTYELLOW_EX}{quoted}{Style.RESET_ALL}")

    def handle_sigint(signum, frame):
        print(Fore.LIGHTRED_EX + "\n[!] interrupted by user, exiting" + Style.RESET_ALL, flush=True)
        os._exit(130)

    signal.signal(signal.SIGINT, handle_sigint)

    fh = FileHandler()
    root_domains = fh.list_root_domains(domain=args.domain, domains_file=args.domains_file)
    resolvers = fh.set_resolvers(resolvers_file=args.resolvers_file, brute_force=args.brute_force, mutation=args.mutation)
    permutation_strings = fh.set_permutation_strings(permutation_file=args.permutation_file)

    mr = ModuleRunner()
    
    while True: # while loop for the --loop argument
        for domain in root_domains:
            start_time = time.time()
            logging.warning(f"[*] snrubing starting for {Fore.LIGHTYELLOW_EX}{domain}")
            results = {}

            if args.disable_scraping:
                logging.warning(f"{Fore.LIGHTYELLOW_EX}[!] scraping disabled")
            else:
                results.update(
                mr.run_scraper(
                    domain=domain,
                    proxy=args.proxy,
                    sources=args.sources,
                    fast=args.fast,
                    output_file=args.output_file,
                    filter_strings=filter_strings
                )
            )

            if args.brute_force:
                subdomains = fh.set_subdomains(domain=domain, subdomains_file=args.subdomains_file)
                results.update(
                mr.run_brute_force(
                    domain=domain,
                    tasks=args.tasks,
                    subdomains=subdomains,
                    resolvers=resolvers,
                    operating_system=os.name,
                    timeout=args.timeout,
                    dns_retries=args.dns_retries,
                    verbosity_level=verbosity_level,
                    output_file=args.output_file,
                    wildcard_evasion=args.wildcard_evasion,
                    filter_strings=filter_strings
                )
            )

            if args.san:
                found_subdomains = {subdomain for enum_data in results.values() for subdomain in enum_data['subdomains']}
                results.update(
                mr.run_san_search(
                    domain=domain,
                    found_subdomains=found_subdomains,
                    timeout=args.timeout,
                    verbosity_level=verbosity_level,
                    output_file=args.output_file,
                    tasks=args.tasks,
                    filter_strings=filter_strings
                )
            )

            if args.mutation:
                found_subdomains = {subdomain for enum_data in results.values() for subdomain in enum_data['subdomains']}
                results.update(
                mr.run_altdns(
                    domain=domain,
                    found_subdomains=found_subdomains,
                    tasks=args.tasks,
                    resolvers=resolvers,
                    permutations=permutation_strings,
                    operating_system=os.name,
                    max_alts=args.max_alts,
                    autopilot=args.autopilot,
                    timeout=args.timeout,
                    dns_retries=args.dns_retries,
                    verbosity_level=verbosity_level,
                    output_file=args.output_file,
                    wildcard_evasion=args.wildcard_evasion,
                    filter_strings=filter_strings
                )
            )

            if args.recursive:
                found_subdomains = {subdomain for enum_data in results.values() for subdomain in enum_data['subdomains']}
                results.update(
                mr.run_recursive_brute_force(
                    domain=domain,
                    found_subdomains=found_subdomains,
                    tasks=args.tasks,
                    resolvers=resolvers,
                    operating_system=os.name,
                    timeout=args.timeout,
                    dns_retries=args.dns_retries,
                    verbosity_level=verbosity_level,
                    words_file=args.recursive_file,
                    depth=args.recursive_depth,
                    output_file=args.output_file,
                    wildcard_evasion=args.wildcard_evasion,
                    filter_strings=filter_strings
                )
            )

            rp = ResultsPrinter(start_time=start_time, results=results)
            rp.print_summary()
            rp.print_finished()

        if not args.loop:
            break

if __name__ == "__main__":
    args = parse_args()
    main(args)