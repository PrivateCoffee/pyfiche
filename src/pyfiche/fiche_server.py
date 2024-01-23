import argparse
import sys
import os
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
    parser.add_argument('-M', '--max_size', type=int, help='Maximum file size (in bytes) (default: 5242880)')
    parser.add_argument('-l', '--log_file', help='Log file path (default: None - log to stdout)')
    parser.add_argument('-b', '--banlist', help='Banlist file path')
    parser.add_argument('-w', '--allowlist', help='Allowlist file path')
    parser.add_argument('-D', '--debug', action='store_true', help='Debug mode')
    parser.add_argument('-t', '--timeout', type=int, help='Timeout for incoming connections (in seconds)')
    parser.add_argument('-u', '--user_name', help=argparse.SUPPRESS)

    # Parse the arguments
    args = parser.parse_args()

    # Get environment variables
    domain = os.environ.get('PYFICHE_DOMAIN', 'localhost')
    port = os.environ.get('PYFICHE_PORT', 9999)
    listen_addr = os.environ.get('PYFICHE_LISTEN_ADDR', '0.0.0.0')
    slug_size = os.environ.get('PYFICHE_SLUG_SIZE', 8)
    https = os.environ.get('PYFICHE_HTTPS', False)
    output_dir = os.environ.get('PYFICHE_OUTPUT_DIR', 'data/')
    buffer_size = os.environ.get('PYFICHE_BUFFER_SIZE', 4096)
    max_size = os.environ.get('PYFICHE_MAX_SIZE', 5242880)
    log_file = os.environ.get('PYFICHE_LOG_FILE', None)
    banlist = os.environ.get('PYFICHE_BANLIST', None)
    allowlist = os.environ.get('PYFICHE_ALLOWLIST', None)
    debug = os.environ.get('PYFICHE_DEBUG', False)
    timeout = os.environ.get('PYFICHE_TIMEOUT', None)

    # Set the arguments
    args.domain = args.domain or domain
    args.port = args.port or int(port)
    args.listen_addr = args.listen_addr or listen_addr
    args.slug_size = args.slug_size or int(slug_size)
    args.https = args.https or bool(https)
    args.output_dir = args.output_dir or output_dir
    args.buffer_size = args.buffer_size or int(buffer_size)
    args.max_size = args.max_size or int(max_size)
    args.log_file = args.log_file or log_file
    args.banlist = args.banlist or banlist
    args.allowlist = args.allowlist or allowlist
    args.debug = args.debug or bool(debug)
    args.timeout = args.timeout or timeout

    # Create a Fiche object
    fiche = FicheServer.from_args(args)

    # Run the server
    fiche.run()

# Check if the script is run directly
if __name__ == '__main__':
    main()
