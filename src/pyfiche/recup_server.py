import argparse
import sys
import os
import threading

from . import RecupServer


# Define the main function
def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(
        description="PyRecup Server - returns files uploaded through PyFiche"
    )

    # Add arguments to the parser
    parser.add_argument(
        "-p", "--port", type=int, help="Port of Recup server (default: 9998)"
    )
    parser.add_argument("-L", "--listen_addr", help="Listen Address (default: 0.0.0.0)")
    parser.add_argument(
        "-o", "--data_dir", help="Fiche server output directory path (default: data/)"
    )
    parser.add_argument(
        "-B", "--buffer_size", type=int, help="Buffer size (default: 16)"
    )  # TODO: Do we *really* need this?
    parser.add_argument(
        "-l", "--log_file", help="Log file path (default: None - log to stdout)"
    )
    parser.add_argument("-b", "--banlist", help="Banlist file path")
    parser.add_argument("-w", "--allowlist", help="Allowlist file path")
    parser.add_argument("-D", "--debug", action="store_true", help="Debug mode")
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        help="Timeout for incoming connections (in seconds)",
    )

    # Parse the arguments
    args = parser.parse_args()

    # Get environment variables
    port = os.environ.get("PYFICHE_RECUP_PORT", 9998)
    listen_addr = os.environ.get(
        "PYFICHE_RECUP_LISTEN_ADDR", os.environ.get("PYFICHE_LISTEN_ADDR", "0.0.0.0")
    )
    data_dir = os.environ.get(
        "PYFICHE_RECUP_DATA_DIR", os.environ.get("PYFICHE_DATA_DIR", "data/")
    )
    buffer_size = os.environ.get("PYFICHE_RECUP_BUFFER_SIZE", 16)
    log_file = os.environ.get(
        "PYFICHE_RECUP_LOG_FILE", os.environ.get("PYFICHE_LOG_FILE", None)
    )
    banlist = os.environ.get(
        "PYFICHE_RECUP_BANLIST", os.environ.get("PYFICHE_BANLIST", None)
    )
    allowlist = os.environ.get(
        "PYFICHE_RECUP_ALLOWLIST", os.environ.get("PYFICHE_ALLOWLIST", None)
    )
    debug = os.environ.get(
        "PYFICHE_RECUP_DEBUG", os.environ.get("PYFICHE_DEBUG", False)
    )
    timeout = os.environ.get("PYFICHE_RECUP_TIMEOUT", None)

    # Set the arguments
    args.port = args.port or int(port)
    args.listen_addr = args.listen_addr or listen_addr
    args.data_dir = args.data_dir or data_dir
    args.buffer_size = args.buffer_size or buffer_size
    args.log_file = args.log_file or log_file
    args.banlist = args.banlist or banlist
    args.allowlist = args.allowlist or allowlist
    args.debug = args.debug or bool(debug)
    args.timeout = args.timeout or timeout

    # Create a Recup object
    recup = RecupServer.from_args(args)

    # Run the server
    recup.run()


# Check if the script is run directly
if __name__ == "__main__":
    main()
