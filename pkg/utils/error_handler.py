import logging
import requests.exceptions
import json.decoder
import sys
import traceback

from colorama import Fore, Back, Style

class ErrorHandler:
    ERROR_MESSAGES = {
        requests.exceptions.Timeout: "Timeout",
        requests.exceptions.RequestException: "Request Exception",
        TypeError: "Type Error",
        AttributeError: "Attribute Error",
        json.decoder.JSONDecodeError: "JSON Decode Error",
        ConnectionError: "Connection Error",
        KeyboardInterrupt: "Keyboard Interrupt",
        NameError: "Name Error",
        type(None): "NoneType Error"
    }

    def handle_error(self, error, source):
        message = self.ERROR_MESSAGES.get(type(error), "Unknown Error")
        if isinstance(error, KeyboardInterrupt):
            logging.debug(f"{Fore.LIGHTRED_EX}[ERROR] {message}")
            sys.exit()
        logging.debug(f"{Fore.LIGHTRED_EX}[ERROR] {source}{Style.RESET_ALL} {message}: {error}")
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            traceback.print_exc()