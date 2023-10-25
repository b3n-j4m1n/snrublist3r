import logging
import urllib3

from colorama import Fore, Style

class Verbosity:
    def level(self, verbose, debug, silent):
        log_levels = {
            0: logging.CRITICAL,
            1: logging.ERROR,
            2: logging.WARN,
            3: logging.INFO,
            4: logging.DEBUG
        }
        count = sum(x is not None for x in [verbose, debug, silent])
        if count > 1:
            raise ValueError(f"{Fore.LIGHTRED_EX}[-] cannot have -v/--verbose, --debug, and/or --silent arguments used together{Style.RESET_ALL}")
        elif verbose is not None:
            logging.getLogger("requests").setLevel(logging.CRITICAL)
            logging.getLogger('urllib3').setLevel(logging.CRITICAL)
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logging.basicConfig(level=log_levels[3], format='%(message)s')
            return 3
        elif debug is not None:
            logging.basicConfig(level=log_levels[4], format='%(message)s')
            return 4
        elif silent is not None:
            logging.getLogger("requests").setLevel(logging.CRITICAL)
            logging.getLogger('urllib3').setLevel(logging.CRITICAL)
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logging.basicConfig(level=log_levels[0], format='%(message)s')
            return 0
        else:
            logging.getLogger("requests").setLevel(logging.CRITICAL)
            logging.getLogger('urllib3').setLevel(logging.CRITICAL)
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logging.basicConfig(level=log_levels[2], format='%(message)s')
            return 2