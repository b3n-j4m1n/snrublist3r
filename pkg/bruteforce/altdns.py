import tldextract

class AltDNS:
    def __init__(self, found_subdomains, permutation_list):
        self.permutations = set()
        self.permutation_list = permutation_list
        self.found_subdomains = found_subdomains

    def insert_all_indexes(self):
        index_results = set()
        for line in self.found_subdomains:
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
            ext = tldextract.extract(line.strip())
            current_sub = ext.subdomain.split(".")
            for word in range(0, 10):
                for index, value in enumerate(current_sub):
                    original_sub = current_sub[index] # admin
                    current_sub[index] = current_sub[index] + "-" + str(word) # ['admin-0']
                    actual_sub = ".".join(current_sub) # admin-0
                    full_url = "{0}.{1}.{2}".format(actual_sub, ext.domain, ext.suffix) # admin-0.example.com
                    number_results.add(full_url)
                    self.permutations.add(full_url)
                    current_sub[index] = original_sub # ['admin']
                    original_sub = current_sub[index] # admin
                    current_sub[index] = current_sub[index] + str(word) # ['admin0']
                    actual_sub = ".".join(current_sub) # admin0
                    full_url = "{0}.{1}.{2}".format(actual_sub, ext.domain, ext.suffix) # admin0.example.com
                    number_results.add(full_url)
                    self.permutations.add(full_url)
                    current_sub[index] = original_sub
        return(number_results)

    def insert_dash_subdomains(self):
        dash_results = set()
        for line in self.found_subdomains:
            ext = tldextract.extract(line.strip())
            current_sub = ext.subdomain.split(".")
            for word in self.permutation_list:
                for index, value in enumerate(current_sub):
                    original_sub = current_sub[index] # admin
                    current_sub[index] = current_sub[index] + "-" + word.strip() # ['admin-staging']
                    actual_sub = ".".join(current_sub) # admin-staging
                    full_url = "{0}.{1}.{2}".format(actual_sub, ext.domain, ext.suffix) # admin-staging.example.com
                    if len(current_sub[0]) > 0 and actual_sub[:1] != "-":
                        dash_results.add(full_url)
                        self.permutations.add(full_url)
                    current_sub[index] = original_sub # ['admin']
                    current_sub[index] = word.strip() + "-" + current_sub[index] # ['staging-admin']
                    actual_sub = ".".join(current_sub) # staging-admin
                    full_url = "{0}.{1}.{2}".format(actual_sub, ext.domain, ext.suffix) # staging-admin.example.com
                    if actual_sub[-1:] != "-":
                        dash_results.add(full_url)
                        self.permutations.add(full_url)
                    current_sub[index] = original_sub
        return(dash_results)

    def join_words_subdomains(self):
        join_results = set()
        for line in self.found_subdomains:
            ext = tldextract.extract(line.strip())
            current_sub = ext.subdomain.split(".")
            for word in self.permutation_list:
                for index, value in enumerate(current_sub):
                    original_sub = current_sub[index] # ['admin']
                    current_sub[index] = current_sub[index] + word.strip() # ['adminstaging']
                    actual_sub = ".".join(current_sub) # adminstaging
                    full_url = "{0}.{1}.{2}".format(actual_sub, ext.domain, ext.suffix) # adminstaging.example.com
                    join_results.add(full_url)
                    self.permutations.add(full_url)
                    current_sub[index] = original_sub # ['admin']
                    current_sub[index] = word.strip() + current_sub[index] # ['stagingadmin']
                    actual_sub = ".".join(current_sub) # stagingadmin
                    full_url = "{0}.{1}.{2}".format(actual_sub, ext.domain, ext.suffix) # stagingadmin.example.com
                    join_results.add(full_url)
                    self.permutations.add(full_url)
                    current_sub[index] = original_sub
        return(join_results)