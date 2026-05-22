# constants.py
# This file contains constants used across the application.
from colorama import Fore, Style, init
init(autoreset=True)

CHUNK_SIZE = 4096
IP = "0.0.0.0"  # change to 127.0.0.1 by need to run client and server on same pc.
PORT = 9951
MAX_TOTAL_CONNECTIONS = 15
MAX_CONNECTIONS_PER_IP = 3

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "NewStrongPassword1!",
    "database": "verifile_db"
}

CYAN = Fore.LIGHTCYAN_EX
GREEN = Fore.LIGHTGREEN_EX
YELLOW = Fore.LIGHTYELLOW_EX
RED = Fore.LIGHTRED_EX
MAGENTA = Fore.LIGHTMAGENTA_EX
BLUE = Fore.LIGHTBLUE_EX
RESET = Style.RESET_ALL
BOLD = Style.BRIGHT
