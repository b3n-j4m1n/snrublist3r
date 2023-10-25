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
                    if cleaned_line:  # avoid adding empty lines
                        root_domains.append(cleaned_line)
        return root_domains
    
    def set_nameservers(self, nameserver_file, brute_force, mutation):
        nameservers = []
        if (brute_force is True or mutation is True) and nameserver_file is None:
            logging.warning(f"{Fore.LIGHTYELLOW_EX}[!] WARNING, -nf/--nameservers-file not set, using system settings (potential DoS)")
        elif  (brute_force is True or mutation is True) and nameserver_file is not None:
            with open(nameserver_file) as file:
                lines = file.readlines()
                nameservers = [line.rstrip() for line in lines]
                logging.info(f"[*] using nameservers {str(nameservers)}")
        return nameservers
    
    def set_permutation_strings(self, permutation_file):
        with open(permutation_file) as file:
            lines = file.readlines()
            permutation_file = [line.rstrip() for line in lines]
        return permutation_file
    
    def set_subdomains(self, domain, subdomains_file):
        with open(subdomains_file) as file:
            line = file.readlines()
            line = [line.rstrip() for line in line]
        subdomains = [subdomain + '.' + domain for subdomain in line]
        return subdomains