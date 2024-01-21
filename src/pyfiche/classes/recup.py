import re
import socket
import pathlib
import logging
import argparse
import ipaddress
import os
import sys
import threading

from typing import Optional, Union

from .fiche import FicheServer

class RecupServer:
    FICHE_SYMBOLS = FicheServer.FICHE_SYMBOLS
    DATA_FILE_NAME = FicheServer.OUTPUT_FILE_NAME
    
    port: int = 9998
    listen_addr: str = '0.0.0.0'
    buffer_size: int = 16
    _data_dir: pathlib.Path = pathlib.Path('data/')
    _log_file: Optional[pathlib.Path] = None
    _banlist: Optional[pathlib.Path] = None
    _allowlist: Optional[pathlib.Path] = None
    logger: Optional[logging.Logger] = None

    @property
    def data_dir(self) -> pathlib.Path:
        return self._data_dir

    @data_dir.setter
    def data_dir(self, value: Union[str, pathlib.Path]) -> None:
        if isinstance(value, str):
            value = pathlib.Path(value)
        self._data_dir = value

    @property
    def data_dir_path(self) -> str:
        return str(self.data_dir.absolute())

    @property
    def log_file(self) -> Optional[pathlib.Path]:
        return self._log_file

    @log_file.setter
    def log_file(self, value: Union[str, pathlib.Path]) -> None:
        if isinstance(value, str):
            value = pathlib.Path(value)
        self._log_file = value

    @property
    def log_file_path(self) -> Optional[str]:
        return str(self.log_file.absolute()) if self.log_file else None

    @property
    def banlist(self) -> Optional[pathlib.Path]:
        return self._banlist

    @banlist.setter
    def banlist(self, value: Union[str, pathlib.Path]) -> None:
        if isinstance(value, str):
            value = pathlib.Path(value)
        self._banlist = value

    @property
    def banlist_path(self) -> Optional[str]:
        return str(self.banlist.absolute()) if self.banlist else None

    @property
    def allowlist(self) -> Optional[pathlib.Path]:
        return self._allowlist

    @allowlist.setter
    def allowlist(self, value: Union[str, pathlib.Path]) -> None:
        if isinstance(value, str):
            value = pathlib.Path(value)
        self._allowlist = value

    @property
    def allowlist_path(self) -> Optional[str]:
        return str(self.allowlist.absolute()) if self.allowlist else None

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> 'RecupServer':
        recup = cls()

        recup.port = args.port or recup.port
        recup.listen_addr = args.listen_addr or recup.listen_addr
        recup.data_dir = args.data_dir or recup.data_dir
        recup.buffer_size = args.buffer_size or recup.buffer_size
        recup.log_file = args.log_file or recup.log_file
        recup.banlist = args.banlist or recup.banlist
        recup.allowlist = args.allowlist or recup.allowlist

        recup.logger = logging.getLogger('pyfiche')
        recup.logger.setLevel(logging.INFO if not args.debug else logging.DEBUG)
        handler = logging.StreamHandler() if not args.log_file else logging.FileHandler(args.log_file)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        recup.logger.addHandler(handler)

        return recup

    def handle_connection(self, conn, addr):
        self.logger.info(f"Incoming connection from: {addr}")

        if self.check_banlist(addr[0]):
            conn.sendall(b"Your IP address is banned from this server.\n")
            self.logger.info(f"Connections from {addr} are banned.")
            conn.close()
            return

        if not self.check_allowlist(addr[0]):
            conn.sendall(b"Your IP address is not allowed to connect to this server.\n")
            self.logger.info(f"Connection from {addr} is not allowed.")
            conn.close()
            return

        conn.setblocking(False)
        conn.settimeout(3)

        with conn:
            self.logger.debug(f"New connection by {addr}")

            if not self.check_allowlist(addr[0]):
                conn.sendall(b"Your IP address is not allowed to connect to this server.\n")
                self.logger.info(f"Connection from {addr} is not allowed.")
                conn.close()
                return

            if self.check_banlist(addr[0]):
                conn.sendall(b"Your IP address is banned from this server.\n")
                self.logger.info(f"Connections from {addr} are banned.")
                conn.close()
                return

            try:
                slug = conn.recv(self.buffer_size).decode().strip()

                if not slug:
                    raise ValueError('No slug received, terminating connection.')

                # Check if the received slug matches the allowed pattern.
                # This should effectively prevent directory traversal attacks.
                if any([c not in self.FICHE_SYMBOLS for c in slug]):
                    raise ValueError('Invalid slug received, terminating connection.')

                file_path = self.data_dir / slug / self.DATA_FILE_NAME
                if not file_path.is_file():
                    raise FileNotFoundError(f"File with slug '{slug}' not found.")

                with open(file_path, 'rb') as file:
                    content = file.read()
                    conn.sendall(content)

            except (ValueError, FileNotFoundError) as e:
                self.logger.error(e)
                conn.close()

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.listen_addr, self.port))
            s.listen()

            self.logger.info(f"Server started listening on: {self.listen_addr}:{self.port}")

            while True:
                conn, addr = s.accept()
                threading.Thread(target=self.handle_connection, args=(conn, addr,)).start()

    def run(self):
        if not self.logger:
            self.logger = logging.getLogger('pyfiche')
            self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler() if not self.log_file else logging.FileHandler(self.log_file)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)

        if self.banlist and self.allowlist:
            self.logger.fatal("Banlist and allowlist cannot be used together!")
            sys.exit(1)

        if self.banlist_path and not os.path.exists(self.banlist_path):
            self.logger.fatal(f"Banlist file ({self.banlist_path}) does not exist!")
            sys.exit(1)

        if self.allowlist_path and not os.path.exists(self.allowlist_path):
            self.logger.fatal(f"Allowlist file ({self.allowlist_path}) does not exist!")
            sys.exit(1)

        self.logger.info(f"Starting PyFiche-Recup...")

        if self.data_dir.exists() and not os.access(self.data_dir_path, os.R_OK):
            self.logger.fatal(f"Data directory ({self.data_dir}) not readable!")
            sys.exit(1)

        elif not self.data_dir.exists():
            self.logger.fatal(f"Data directory ({self.data_dir}) does not exist!")
            sys.exit(1)

        if self.log_file_path:
            try:
                with open(self.log_file_path, 'a'):
                    pass
            except IOError:
                self.logger.fatal("Log file not writable!")
                sys.exit(1)

        self.start_server()

        return 0

    def check_allowlist(self, addr):
        if not self.allowlist_path:
            return True

        try:
            ip = ipaddress.ip_address(addr)
            with open(self.allowlist_path, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        network = ipaddress.ip_network(line, strict=False)
                        if ip in network:
                            return True
        except ValueError as e:
            self.logger.error(f"Invalid IP address or network: {e}")
            return False

        return False

    def check_banlist(self, addr):
        if not self.banlist_path:
            return False

        try:
            ip = ipaddress.ip_address(addr)
            with open(self.banlist_path, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        network = ipaddress.ip_network(line, strict=False)
                        if ip in network:
                            return True
        except ValueError as e:
            self.logger.error(f"Invalid IP address or network: {e}")
            return False

        return False