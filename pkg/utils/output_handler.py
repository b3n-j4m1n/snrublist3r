import os

class OutputHandler:
    def handle_output(self, output_file, results):
        running_results = set()

        # reading output file into a set
        if os.path.isfile(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                running_results = set(line.strip() for line in f)

        # checking incoming module results for subdomains that haven't already been found
        new_results = set()
        for key in results.keys():
            for subdomain in results[key]['subdomains']:
                if subdomain not in running_results:
                    new_results.add(subdomain)

        # appending new subdomains to the output file
        with open(output_file, 'a', encoding='utf-8') as f:
            for domain in new_results:
                f.write(f"{domain}\n")