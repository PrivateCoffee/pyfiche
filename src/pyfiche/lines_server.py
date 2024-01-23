import argparse
import sys
import os
import threading

from . import LinesServer

# Define the main function
def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description='PyFiche Lines - HTTP server for PyFiche')

    # Add arguments to the parser
    parser.add_argument('-p', '--port', type=int, help='Port of Recup server (default: 9997)')
    parser.add_argument('-L', '--listen_addr', help='Listen Address (default: 0.0.0.0)')
    parser.add_argument('-o', '--data_dir', help='Fiche server output directory path (default: data/)')
    parser.add_argument('-l', '--log_file', help='Log file path (default: None - log to stdout)')
    parser.add_argument('-b', '--banlist', help='Banlist file path')
    parser.add_argument('-w', '--allowlist', help='Allowlist file path')
    parser.add_argument('-M', '--max_size', type=int, help='Maximum file size (in bytes) (default: 5242880)')
    parser.add_argument('-D', '--debug', action='store_true', help='Debug mode')

    # Parse the arguments
    args = parser.parse_args()

    # Get environment variables
    port = os.environ.get('PYFICHE_LINES_PORT', 9997)
    listen_addr = os.environ.get('PYFICHE_LINES_LISTEN_ADDR', os.environ.get('PYFICHE_LISTEN_ADDR', '0.0.0.0'))
    data_dir = os.environ.get('PYFICHE_LINES_DATA_DIR', os.environ.get('PYFICHE_DATA_DIR', 'data/'))
    log_file = os.environ.get('PYFICHE_LINES_LOG_FILE', os.environ.get('PYFICHE_LOG_FILE', None))
    banlist = os.environ.get('PYFICHE_LINES_BANLIST', os.environ.get('PYFICHE_BANLIST', None))
    allowlist = os.environ.get('PYFICHE_LINES_ALLOWLIST', os.environ.get('PYFICHE_ALLOWLIST', None))
    max_size = os.environ.get('PYFICHE_LINES_MAX_SIZE', os.environ.get('PYFICHE_MAX_SIZE', 5242880))
    debug = os.environ.get('PYFICHE_LINES_DEBUG', os.environ.get('PYFICHE_DEBUG', False))    

    # Set the arguments
    args.port = args.port or int(port)
    args.listen_addr = args.listen_addr or listen_addr
    args.data_dir = args.data_dir or data_dir
    args.log_file = args.log_file or log_file
    args.banlist = args.banlist or banlist
    args.allowlist = args.allowlist or allowlist
    args.max_size = args.max_size or max_size
    args.debug = args.debug or bool(debug)

    # Create a Lines object
    lines = LinesServer.from_args(args)

    # Run the server
    lines.run()

# Check if the script is run directly
if __name__ == '__main__':
    main()
