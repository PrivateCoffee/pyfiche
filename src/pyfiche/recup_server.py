import argparse
import sys
import threading

from . import RecupServer

# Define the main function
def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description='PyRecup Server - returns files uploaded through PyFiche')

    # Add arguments to the parser
    parser.add_argument('-p', '--port', type=int, help='Port of Recup server (default: 9998)')
    parser.add_argument('-L', '--listen_addr', help='Listen Address (default: 0.0.0.0)')
    parser.add_argument('-o', '--data_dir', help='Fiche server output directory path (default: data/)')
    parser.add_argument('-B', '--buffer_size', type=int, help='Buffer size (default: 16)') # TODO: Do we *really* need this?
    parser.add_argument('-l', '--log_file', help='Log file path (default: None - log to stdout)')
    parser.add_argument('-b', '--banlist', help='Banlist file path')
    parser.add_argument('-w', '--allowlist', help='Allowlist file path')
    parser.add_argument('-D', '--debug', action='store_true', help='Debug mode')
    parser.add_argument('-t', '--timeout', type=int, help='Timeout for incoming connections (in seconds)')

    # Parse the arguments
    args = parser.parse_args()

    # Create a Recup object
    recup = RecupServer.from_args(args)

    # Run the server
    recup.run()

# Check if the script is run directly
if __name__ == '__main__':
    main()
