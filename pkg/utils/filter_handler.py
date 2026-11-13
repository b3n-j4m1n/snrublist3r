def parse_filter_strings(filter_string_arg):
    # normalizes the -fs/--filter-string argument(s) into a lowercase list,
    # supports repeatable arguments and/or comma-separated values, e.g.
    # -fs ".crm." -fs ".foo." or -fs ".crm., .foo."
    if not filter_string_arg:
        return []
    filter_strings = []
    for value in filter_string_arg:
        for item in value.split(','):
            item = item.strip().lower()
            if item and item not in filter_strings:
                filter_strings.append(item)
    return filter_strings


def is_filtered(subdomain, filter_strings):
    # case-insensitive substring match against the configured filter strings
    if not filter_strings:
        return False
    subdomain = subdomain.lower()
    return any(filter_string in subdomain for filter_string in filter_strings)
