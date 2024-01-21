import argparse
import sys
import threading

from . import FicheServer

# Define the main function
def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description='PyFiche Server - upload and share files through the terminal')

    # Add arguments to the parser
    parser.add_argument('-d', '--domain', help='Domain to use in URLs (default: localhost)')
    parser.add_argument('-p', '--port', type=int, help='Port of Fiche server (default: 9999)')
    parser.add_argument('-L', '--listen_addr', help='Listen Address (default: 0.0.0.0)')
    parser.add_argument('-s', '--slug_size', type=int, help='Length of slugs to generate (default: 8)')
    parser.add_argument('-S', '--https', action='store_true', help='HTTPS (requires reverse proxy)')
    parser.add_argument('-o', '--output_dir', help='Output directory path (default: data/)')
    parser.add_argument('-B', '--buffer_size', type=int, help='Buffer size (default: 4096)')
    parser.add_argument('-l', '--log_file', help='Log file path (default: None - log to stdout)')
    parser.add_argument('-b', '--banlist', help='Banlist file path')
    parser.add_argument('-w', '--allowlist', help='Allowlist file path')
    parser.add_argument('-D', '--debug', action='store_true', help='Debug mode')
    parser.add_argument('-t', '--timeout', type=int, help='Timeout for incoming connections (in seconds)')
    parser.add_argument('-u', '--user_name', help=argparse.SUPPRESS)

    # Parse the arguments
    args = parser.parse_args()

    # Create a Fiche object
    fiche = FicheServer.from_args(args)

    # Run the server
    fiche.run()

# Check if the script is run directly
if __name__ == '__main__':
    main()
