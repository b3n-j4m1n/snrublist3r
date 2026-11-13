import logging

from colorama import Fore, Back, Style

class FileHandler:
    def list_root_domains(self, domain, domains_file):
        root_domains = []
        if domain is not None and domains_file is not None:
            raise ValueError(f"{Fore.LIGHTRED_EX}[-] cannot have both -d/--domain and -df/--domains-file arguments")
        if domain is None and domains_file is None:
            raise ValueError(f"{Fore.LIGHTRED_EX}[-] -d/--domain or -df/--domains-file argument required")
        if domain is not None:
            root_domains.append(domain)
        if domains_file is not None:
            with open(domains_file) as file:
                lines = file.readlines()
                for line in lines:
                    cleaned_line = line.rstrip()
                    if cleaned_line: # avoid adding empty lines
                        root_domains.append(cleaned_line)
        return root_domains
    
    def set_resolvers(self, resolvers_file, brute_force, mutation):
        resolvers = []
        if (brute_force is True or mutation is True) and resolvers_file is None:
            logging.warning(f"{Fore.LIGHTYELLOW_EX}[!] WARNING, -rf/--resolvers-file not set, using system settings (potential DoS)")
        elif  (brute_force is True or mutation is True) and resolvers_file is not None:
            with open(resolvers_file) as file:
                lines = file.readlines()
                resolvers = [line.rstrip() for line in lines]
                logging.info(f"[*] using resolvers {Fore.LIGHTYELLOW_EX}{str(resolvers)}{Style.RESET_ALL}")
        return resolvers
    
    def set_permutation_strings(self, permutation_file):
        with open(permutation_file) as file:
            lines = file.readlines()
            permutation_file = [line.rstrip() for line in lines]
        return permutation_file
    
    def set_subdomains(self, domain, subdomains_file):
        subdomains = []
        seen = set() # O(1) membership tracking, the list append preserves order
        with open(subdomains_file) as file:
            for line in file:
                subdomain = line.strip().lower()
                if not subdomain or subdomain.startswith('#'):
                    continue
                if subdomain.startswith('*.'):
                    subdomain = subdomain[2:]
                if subdomain == '*':
                    continue
                if subdomain.endswith('.' + domain):
                    subdomain = subdomain[:-(len(domain) + 1)]
                if subdomain and subdomain not in seen:
                    seen.add(subdomain)
                    subdomains.append(subdomain)
        return [subdomain + '.' + domain for subdomain in subdomains]