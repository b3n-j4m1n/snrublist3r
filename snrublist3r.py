import argparse
import colorama
from colorama import Fore, Back, Style
import logging
import os
import random
import requests
import string
import socket
import time
import warnings
from pkg.bruteforce import altdns, dnsbruteforce
from pkg.scrape import (
    alienvault,
    anubis,
    ask,
    bing,
    certificatesearch,
    dnsdumpster,
    duckduckgo,
    gist,
    google,
    hackertarget,
    rapiddns,
    sonarsearch,
    threatcrowd,
    threatminer,
    virustotal,
    waybackmachine,
    yahoo,
)


def start_scraper(root_domains, proxy, sources, autopilot):
    warnings.filterwarnings("ignore", category=UserWarning, module='bs4')
    requests.packages.urllib3.disable_warnings()
    results = set()
    sources_selected = []
    sources_modules = {
        'alienvault': alienvault.AlienVault(root_domains, proxy),
        'anubis': anubis.Anubis(root_domains, proxy),
        'ask': ask.Ask(root_domains, proxy),
        'bing': bing.Bing(root_domains, proxy),
        'certificatesearch': certificatesearch.CertificateSearch(root_domains, proxy),
        'dnsdumpster': dnsdumpster.DNSDumpster(root_domains, proxy),
        'duckduckgo': duckduckgo.DuckDuckGo(root_domains, proxy),
        'gist': gist.Gist(root_domains, proxy),
        'google': google.Google(root_domains, proxy, autopilot),
        'hackertarget': hackertarget.HackerTarget(root_domains, proxy),
        'rapiddns': rapiddns.RapidDNS(root_domains, proxy),
        'sonarsearch': sonarsearch.SonarSearch(root_domains, proxy),
        'threatcrowd': threatcrowd.ThreatCrowd(root_domains, proxy),
        'threatminer': threatminer.ThreatMiner(root_domains, proxy),
        'virustotal': virustotal.VirusTotal(root_domains, proxy),
        'waybackmachine': waybackmachine.WaybackMachine(root_domains, proxy),
        'yahoo': yahoo.Yahoo(root_domains, proxy)
    }
    sources_names = {
        'alienvault': "AlienVault",
        'anubis': "Anubis",
        'ask': "Ask",
        'bing': "Bing",
        'certificatesearch': "Certificate Search",
        'duckduckgo': "DuckDuckGo",
        'dnsdumpster': "DNSDumpster",
        'gist': "Gist",
        'google': "Google",
        'hackertarget': "Hacker Target",
        'rapiddns': "RapidDNS",
        'sonarsearch': "SonarSearch",
        'threatcrowd': "ThreatCrowd",
        'threatminer': "ThreatMiner",
        'virustotal': "VirusTotal",
        'waybackmachine': "Wayback Machine",
        'yahoo': "Yahoo"
    }
    # checking if arg -s values are valid sources
    if all(source in sources_modules for source in sources):
        pass
    else:
        for source in sources:
            if source not in sources_modules:
                logging.error(Fore.LIGHTRED_EX + "[-] unknown source " + source)
        exit()
    # creating a list of source modules to run
    for source in sources:
        if source in sources_names:
            sources_selected.append(sources_names[source])
    logging.info("[*] starting source scraper for sources " + str(sources_selected))
    # running selected source modules and updating the results
    for source in sources:
        results.update(set().union(sources_modules[source].run()))
    return(results)


def start_bruteforce(domain, tasks, subdomain_file, nameservers, operating_system):
    logging.info("[*] starting raw brute force...")
    letters = string.ascii_lowercase
    random_sub = ''.join(random.choice(letters) for _ in range(10))
    try:
        socket.gethostbyname(random_sub + "." + domain)
        logging.error(Fore.LIGHTRED_EX + "[-] wildcard subdomain detected, skipping raw brute force")
        return set()
    except:
        pass
    with open(subdomain_file) as file:
        line = file.readlines()
        line = [line.rstrip() for line in line]
    domain_list = [subdomain + '.' + domain for subdomain in line]
    dnsbf = dnsbruteforce.DNSBruteForce(tasks, nameservers, operating_system)
    results = dnsbf.run(domain_list)
    return results


def start_altdns(known_subdomains, tasks, nameservers, permutations, operating_system, max_alts):
    if len(known_subdomains) > max_alts:
        logging.error(Fore.LIGHTRED_EX + "[-] mutation brute force cancelled, excessive permutations, use --max-alts to override")
        return set()
    logging.info("[*] mutating known subdomains")
    adns = altdns.AltDNS(known_subdomains, permutations)
    domain_list = set().union(
        adns.insert_all_indexes(),
        adns.insert_number_suffix_subdomains(),
        adns.insert_dash_subdomains(),
        adns.join_words_subdomains()
        )
    adns.alt_domain_list.update(domain_list)
    logging.info("[*] " + str(len(adns.alt_domain_list)) + " subdomain mutations generated")
    if args.autopilot is True:
        pass
    else:
        print(Fore.LIGHTYELLOW_EX + "[?] continue with mutation brute force (y/n)? ", end='') # input() doesn't work with colorama
        altdns_length_prompt = input()
        if altdns_length_prompt == ("n"):
            logging.info("[*] mutation brute force cancelled")
            return set()
        elif altdns_length_prompt != ("y"):
            logging.error(Fore.LIGHTRED_EX + "[-] invalid response")
            return set()
        else:
            logging.info("[*] starting mutation brute force...")
            pass
    dnsbf = dnsbruteforce.DNSBruteForce(tasks, nameservers, operating_system)
    results = dnsbf.run(domain_list)
    return results

def start_recursive(known_subdomains, tasks, subdomain_file, nameservers, permutations, operating_system, bruteforce=False, mutation=False):
    results = set()
    recursive_input = known_subdomains.copy()
    loop_input = set()
    for i in range(1, 3):
        logging.info("[*] recursive loop " + str(i) + "/3")
        for domain in recursive_input:
            logging.info("[*] root domain set to " + domain)
            if bruteforce:
                bruteforce_loop_results = start_bruteforce(domain, tasks, subdomain_file, nameservers, operating_system)
                loop_input.update(bruteforce_loop_results)
                results.update(bruteforce_loop_results)
            if mutation:
                mutation_loop_results = (start_altdns(domain, tasks, nameservers, permutations, operating_system))
                loop_input.update(mutation_loop_results)
                results.update(mutation_loop_results)
        if len(loop_input) == 0:
            break
        recursive_input.clear()
        recursive_input.update(loop_input)
        loop_input.clear()
    return results


def output(domain, results):
    output_file = (time.strftime("%Y%m%d%H%M%S") + "_" + domain + ".txt")
    with open(output_file, 'w') as f:
        f.write('\n'.join(str(line) for line in results))
    logging.info("[*] results saved to " + str(output_file))


def verbosity(level):
    logging.getLogger("requests").setLevel(logging.CRITICAL)
    log_levels = {
        0: logging.CRITICAL,
        1: logging.ERROR,
        2: logging.WARN,
        3: logging.INFO,
        4: logging.DEBUG
    }
    logging.basicConfig(level=log_levels[level], format='%(message)s')


def set_root_domains(domain, list):
    root_domains = set()
    if domain is not None and list is not None:
        logging.error(Fore.LIGHTRED_EX + "[-] cannot have both -d/--domain and -l/--list arguements")
        exit()
    if domain is None and list is None:
        logging.error(Fore.LIGHTRED_EX + "[-] -d/--domain or -l/--list arguement required")
        exit()
    if domain is not None:
        root_domains.add(domain)
    if list is not None:
        with open(list) as file:
            lines = file.readlines()
            for line in lines:
                root_domains.add(line.rstrip())
    return(root_domains)


def set_nameservers(nameserver_file):
    nameservers = []
    if (args.bruteforce is True or args.mutation is True) and nameserver_file is None:
        logging.warning(Fore.LIGHTYELLOW_EX + "[!] WARNING, [-n NAMESERVERS] not set, using system settings (potential DoS)") 
    elif  (args.bruteforce is True or args.mutation is True) and nameserver_file is not None:
        with open(nameserver_file) as file:
            lines = file.readlines()
            nameservers = [line.rstrip() for line in lines]
            logging.info("[*] using nameservers " + str(nameservers))
    else:
        pass
    return(nameservers)


def set_permutations(permutation_file):
    with open(permutation_file) as file:
        lines = file.readlines()
        permutations = [line.rstrip() for line in lines]
    return(permutations)


def banner():
    print("""
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
    input = parser.add_argument_group('INPUT')
    source = parser.add_argument_group('SOURCE')
    rate_limit = parser.add_argument_group('RATE-LIMIT')
    output = parser.add_argument_group('OUTPUT')
    configuration = parser.add_argument_group('CONFIGURATION')
    debug = parser.add_argument_group('DEBUG')
    input.add_argument("-d", "--domain", dest="domain", help="domain root", default=None)
    input.add_argument("-l", "--list", dest="list", help="input file of line-separated domains", default=None)
    input.add_argument("-b", dest="bruteforce", help="enable raw brute force", action="store_true")
    input.add_argument("--subdomains", dest="subdomain_file", help="input file of line-separated subdomains used in the DNS brute force (default is bitquark-subdomains-top100000.txt)", default="./lists/bitquark-subdomains-top100000.txt")
    input.add_argument("-m", dest="mutation", help="enable mutation brute force", action="store_true")
    input.add_argument("-p", "--permutations", dest="permutation_file", help="input file of line-separated permutations used in the mutation DNS brute force (default is permutations.txt)", default="./lists/permutations.txt")
    input.add_argument("-n", "--nameservers", dest="nameserver_file", help="input file of line-separated nameserver IPs used in the DNS brute force")
    rate_limit.add_argument("-t", "--tasks", dest="tasks", help="number of concurrent tasks in the brute force queue (default is 512)", type=int, default=512)
    output.add_argument("-o", "--output", dest="output", help="enabled TXT output file to save results, default filename \"time+domain.txt\"", action="store_true")
    debug.add_argument("-v", dest="verbosity", action="count", help="enable vebosity", default=2)
    configuration.add_argument("--proxy", dest="proxy", help="proxy used for source scraper", default=None)
    configuration.add_argument("--autopilot", dest="autopilot", help="ignore input() prompts", action="store_true")
    configuration.add_argument("--max-alts", dest="max_alts", help="generated mutations limit, which if exceeded mutation brute force will not run (useful with --autopilot), default is ~500,000", default=1000000)
    configuration.add_argument("--recursive", dest="recursive", help="enable recursive brute force", action="store_true")
    source.add_argument("-s", "--sources", dest="sources", help="comma-separated list of sources, options are alienvault, anubis, ask, bing, certificatesearch, dnsdumpster, duckduckgo, gist, google, hackertarget, rapiddns, sonarsearch, threatcrowd, threatminer, virustotal, waybackmachine, yahoo (default is all)", default="alienvault,anubis,ask,bing,certificatesearch,dnsdumpster,duckduckgo,gist,google,hackertarget,rapiddns,sonarsearch,threatcrowd,threatminer,virustotal,waybackmachine,yahoo")
    source.add_argument("--disable-scraping", dest="disable_scraping", help="disable scraping of any sources (use with brute force options)", action="store_true") 
    args = parser.parse_args()
    return args


def main(args):
    start_time = time.time()
    colorama.init(autoreset=True)
    banner()
    results = set()
    operating_system = os.name
    if args.verbosity:
        level = args.verbosity
        verbosity(level)
    root_domains = set_root_domains(args.domain, args.list)
    nameservers = set_nameservers(args.nameserver_file)
    tasks = args.tasks
    subdomain_file = args.subdomain_file
    permutations = set_permutations(args.permutation_file)
    max_alts = int(args.max_alts) // 1425
    proxy = args.proxy
    sources = args.sources.split(',')

    for domain in root_domains: 
        if not args.disable_scraping:
            results.update(start_scraper(domain, proxy, sources, args.autopilot))

        if args.bruteforce:
            results.update(start_bruteforce(domain, tasks, subdomain_file, nameservers, operating_system))

        if args.mutation:
            known_subdomains = results
            results.update(start_altdns(known_subdomains, tasks, nameservers, permutations, operating_system, max_alts))

        if args.recursive:
            known_subdomains = results
            results.update(start_recursive(known_subdomains, tasks, subdomain_file, nameservers, permutations, operating_system, args.bruteforce, args.mutation))

        if args.output:
            output(domain, results)

        for result in results:
            logging.info(Fore.LIGHTWHITE_EX + result)
        logging.info(Fore.LIGHTCYAN_EX + "[*] " + str(len(results)) + " total subdomains discovered for " + domain + " in " + str(round((time.time() - start_time), 2)) + " seconds")
        results.clear()

if __name__ == "__main__":
    args = parse_args()
    main(args)
