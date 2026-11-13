import re

import tldextract

# numbers used by insert_number_suffix_subdomains, common small numbers,
# service/round numbers and recent years
NUMERIC_WORDS = [str(number) for number in range(1, 31)] + [
    '50', '100', '101', '143', '443', '445', '465', '587', '993', '995',
    '1080', '1433', '3000', '3306', '3389', '4000', '5000', '5432', '5900',
    '6379', '8000', '8080', '8081', '8443', '8888', '9000', '9090',
] + [str(year) for year in range(2023, 2041)]

# matches an optional dash followed by trailing digits, e.g. api-1, api1, api12
TRAILING_NUMBER_PATTERN = re.compile(r'^(?P<prefix>.*?)(?P<separator>-?)(?P<number>\d+)$')

INCREMENT_WINDOW = 5 # numbered found hosts also generate suffixes within +/- this range
MAX_ADAPTIVE_WORDS = 250 # upper bound on adaptive words harvested from found subdomains

class AltDNS:
    def __init__(self, found_subdomains, permutation_list, max_mutations=None):
        self.permutations = set()
        self.permutation_list = permutation_list
        self.found_subdomains = found_subdomains
        # shared hard cap on the total number of generated mutations, once it is
        # reached every generator stops early so an excessive found-subdomain list
        # cannot exhaust memory; None means unlimited
        self.max_mutations = max_mutations
        self.cap_hit = False

    def cap_reached(self):
        if self.max_mutations is not None and len(self.permutations) >= self.max_mutations:
            self.cap_hit = True
            return True
        return False

    def insert_all_indexes(self):
        index_results = set()
        for line in self.found_subdomains:
            if self.cap_reached():
                break
            ext = tldextract.extract(line.strip()) # e.g., ExtractResult(subdomain='admin', domain='example', suffix='com')
            current_sub = ext.subdomain.split(".") # e.g., ['admin']
            for word in self.permutation_list:
                for index in range(0, len(current_sub)):
                    current_sub.insert(index, word.strip()) # e.g., ['staging', 'admin']
                    actual_sub = ".".join(current_sub) # e.g., staging.admin
                    full_url = "{0}.{1}.{2}".format(actual_sub, ext.domain, ext.suffix) # e.g., staging.admin.example.com
                    if actual_sub[-1:] != ".":
                        index_results.add(full_url)
                        self.permutations.add(full_url)
                    current_sub.pop(index) # e.g., ['admin']
                current_sub.append(word.strip()) # e.g., ['admin', 'staging']
                actual_sub = ".".join(current_sub) # e.g., admin.staging
                full_url = "{0}.{1}.{2}".format(actual_sub, ext.domain, ext.suffix) # e.g., admin.staging.example.com
                if len(current_sub[0]) > 0:
                    index_results.add(full_url)
                    self.permutations.add(full_url)
                current_sub.pop() # e.g., ['admin']
        return(index_results)

    def insert_number_suffix_subdomains(self):
        number_results = set()
        for line in self.found_subdomains:
            if self.cap_reached():
                break
            ext = tldextract.extract(line.strip()) # e.g., ExtractResult(subdomain='admin', domain='example', suffix='com')
            current_sub = ext.subdomain.split(".") # e.g., ['admin']
            for word in NUMERIC_WORDS: # e.g., '1'
                for index, value in enumerate(current_sub):
                    original_sub = current_sub[index] # e.g., 'admin'
                    current_sub[index] = current_sub[index] + "-" + word # e.g., ['admin-1']
                    actual_sub = ".".join(current_sub) # e.g., admin-1
                    full_url = "{0}.{1}.{2}".format(actual_sub, ext.domain, ext.suffix) # e.g., admin-1.example.com
                    number_results.add(full_url)
                    self.permutations.add(full_url)
                    current_sub[index] = original_sub # e.g., ['admin']
                    current_sub[index] = current_sub[index] + word # e.g., ['admin1']
                    actual_sub = ".".join(current_sub) # e.g., admin1
                    full_url = "{0}.{1}.{2}".format(actual_sub, ext.domain, ext.suffix) # e.g., admin1.example.com
                    number_results.add(full_url)
                    self.permutations.add(full_url)
                    current_sub[index] = original_sub # e.g., ['admin']
        return(number_results)

    def insert_dash_subdomains(self):
        dash_results = set()
        for line in self.found_subdomains:
            if self.cap_reached():
                break
            ext = tldextract.extract(line.strip()) # e.g., ExtractResult(subdomain='admin', domain='example', suffix='com')
            current_sub = ext.subdomain.split(".") # e.g., ['admin']
            for word in self.permutation_list: # e.g., 'staging'
                for index, value in enumerate(current_sub):
                    original_sub = current_sub[index] # e.g., 'admin'
                    current_sub[index] = current_sub[index] + "-" + word.strip() # e.g., ['admin-staging']
                    actual_sub = ".".join(current_sub) # e.g., admin-staging
                    full_url = "{0}.{1}.{2}".format(actual_sub, ext.domain, ext.suffix) # e.g., admin-staging.example.com
                    if len(current_sub[0]) > 0 and actual_sub[:1] != "-":
                        dash_results.add(full_url)
                        self.permutations.add(full_url)
                    current_sub[index] = original_sub # e.g., ['admin']
                    current_sub[index] = word.strip() + "-" + current_sub[index] # e.g., ['staging-admin']
                    actual_sub = ".".join(current_sub) # e.g., staging-admin
                    full_url = "{0}.{1}.{2}".format(actual_sub, ext.domain, ext.suffix) # e.g., staging-admin.example.com
                    if actual_sub[-1:] != "-":
                        dash_results.add(full_url)
                        self.permutations.add(full_url)
                    current_sub[index] = original_sub # e.g., ['admin']
        return(dash_results)

    def join_words_subdomains(self):
        join_results = set()
        for line in self.found_subdomains:
            if self.cap_reached():
                break
            ext = tldextract.extract(line.strip()) # e.g., ExtractResult(subdomain='admin', domain='example', suffix='com')
            current_sub = ext.subdomain.split(".") # e.g., ['admin']
            for word in self.permutation_list: # e.g., 'staging'
                for index, value in enumerate(current_sub):
                    original_sub = current_sub[index] # e.g., ['admin']
                    current_sub[index] = current_sub[index] + word.strip() # e.g., ['adminstaging']
                    actual_sub = ".".join(current_sub) # e.g., adminstaging
                    full_url = "{0}.{1}.{2}".format(actual_sub, ext.domain, ext.suffix) # e.g., adminstaging.example.com
                    join_results.add(full_url)
                    self.permutations.add(full_url)
                    current_sub[index] = original_sub # e.g., ['admin']
                    current_sub[index] = word.strip() + current_sub[index] # e.g., ['stagingadmin']
                    actual_sub = ".".join(current_sub) # e.g., stagingadmin
                    full_url = "{0}.{1}.{2}".format(actual_sub, ext.domain, ext.suffix) # e.g., stagingadmin.example.com
                    join_results.add(full_url)
                    self.permutations.add(full_url)
                    current_sub[index] = original_sub # e.g., ['admin']
        return(join_results)

    def increment_number_suffix_subdomains(self):
        number_results = set()
        for line in self.found_subdomains:
            if self.cap_reached():
                break
            ext = tldextract.extract(line.strip()) # e.g., ExtractResult(subdomain='api2', domain='example', suffix='com')
            current_sub = ext.subdomain.split(".") # e.g., ['api2']
            for index, value in enumerate(current_sub):
                match = TRAILING_NUMBER_PATTERN.match(value) # e.g., prefix='api', separator='', number=2
                if match is None:
                    continue
                prefix = match.group('prefix') # e.g., 'api'
                separator = match.group('separator') # e.g., '' or '-'
                number = int(match.group('number')) # e.g., 2
                for new_number in range(number - INCREMENT_WINDOW, number + INCREMENT_WINDOW + 1): # e.g., -3 to 7
                    if new_number < 0 or new_number == number:
                        continue
                    original_sub = current_sub[index] # e.g., 'api2'
                    current_sub[index] = prefix + separator + str(new_number) # e.g., ['api1'] or ['api3']
                    actual_sub = ".".join(current_sub) # e.g., api3
                    full_url = "{0}.{1}.{2}".format(actual_sub, ext.domain, ext.suffix) # e.g., api3.example.com
                    number_results.add(full_url)
                    self.permutations.add(full_url)
                    current_sub[index] = original_sub # e.g., ['api2']
        return(number_results)

    def replace_component_subdomains(self):
        # replaces a component of the subdomain with a word from the permutation
        # list, e.g. dev -> staging, admin -> mail
        replace_results = set()
        for line in self.found_subdomains:
            if self.cap_reached():
                break
            ext = tldextract.extract(line.strip()) # e.g., ExtractResult(subdomain='admin', domain='example', suffix='com')
            current_sub = ext.subdomain.split(".") # e.g., ['admin']
            for index, value in enumerate(current_sub):
                for word in self.permutation_list: # e.g., 'staging'
                    word = word.strip()
                    if not word or word == value:
                        continue
                    original_sub = current_sub[index] # e.g., 'admin'
                    current_sub[index] = word # e.g., ['staging']
                    actual_sub = ".".join(current_sub) # e.g., staging
                    full_url = "{0}.{1}.{2}".format(actual_sub, ext.domain, ext.suffix) # e.g., staging.example.com
                    if len(current_sub[0]) > 0:
                        replace_results.add(full_url)
                        self.permutations.add(full_url)
                    current_sub[index] = original_sub # e.g., ['admin']
        return(replace_results)

    def merge_adjacent_subdomains(self):
        # merges adjacent components with a dash, e.g. dev.api -> dev-api
        merge_results = set()
        for line in self.found_subdomains:
            if self.cap_reached():
                break
            ext = tldextract.extract(line.strip()) # e.g., ExtractResult(subdomain='dev.api', domain='example', suffix='com')
            current_sub = ext.subdomain.split(".") # e.g., ['dev', 'api']
            for index in range(0, len(current_sub) - 1):
                merged_sub = list(current_sub) # e.g., ['dev', 'api']
                merged_sub[index] = current_sub[index] + "-" + current_sub[index + 1] # e.g., ['dev-api', 'api']
                merged_sub.pop(index + 1) # e.g., ['dev-api']
                if any(len(part) == 0 for part in merged_sub):
                    continue
                actual_sub = ".".join(merged_sub) # e.g., dev-api
                full_url = "{0}.{1}.{2}".format(actual_sub, ext.domain, ext.suffix) # e.g., dev-api.example.com
                merge_results.add(full_url)
                self.permutations.add(full_url)
        return(merge_results)

    @staticmethod
    def harvest_adaptive_words(found_subdomains, permutation_list):
        # harvests adaptive permutation words from the found subdomains
        # themselves: the brand, full labels, and label chunks split on
        # non-alphabetic characters, so discovered naming conventions
        # (e.g. admin-api -> admin, api) feed back into mutation generation
        words = set()
        static = {word.strip().lower() for word in permutation_list}
        for line in found_subdomains:
            ext = tldextract.extract(line.strip()) # e.g., ExtractResult(subdomain='admin-api', domain='example', suffix='com')
            if ext.domain and len(ext.domain) >= 2:
                words.add(ext.domain.lower()) # e.g., 'example' - the brand itself
            for label in ext.subdomain.split("."):
                label = label.lower()
                if len(label) >= 2 and re.match(r"^[a-z0-9-]+$", label):
                    words.add(label) # e.g., 'admin-api' - full labels
                for word in re.split(r"[^a-z]+", label):
                    if len(word) >= 2:
                        words.add(word) # e.g., 'admin', 'api' - label chunks
        return sorted(words - static)[:MAX_ADAPTIVE_WORDS] # e.g., ['admin', 'admin-api', 'api', ...] capped at MAX_ADAPTIVE_WORDS