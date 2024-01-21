import pathlib
import os
import socket
import time
import datetime
import threading
import random
import string
import logging
import ipaddress

from typing import Optional, Tuple

class FicheServer:
    FICHE_SYMBOLS = string.ascii_letters + string.digits
    OUTPUT_FILE_NAME = 'index.txt'

    domain: str = 'localhost'
    port: int = 9999
    listen_addr: str = '0.0.0.0'
    slug_size: int = 8
    https: bool = False
    buffer_size: int = 4096
    _output_dir: pathlib.Path = pathlib.Path('data/')
    _log_file: Optional[pathlib.Path] = None
    _banlist: Optional[pathlib.Path] = None
    _allowlist: Optional[pathlib.Path] = None
    logger: Optional[logging.Logger] = None

    @property
    def output_dir(self) -> pathlib.Path:
        return self._output_dir

    @output_dir.setter
    def output_dir(self, value: str|pathlib.Path) -> None:
        self._output_dir = pathlib.Path(value) if isinstance(value, str) else value

    @property
    def output_dir_path(self) -> str:
        return str(self.output_dir.absolute())

    @property
    def log_file(self) -> Optional[pathlib.Path]:
        return self._log_file

    @log_file.setter
    def log_file(self, value: str|pathlib.Path) -> None:
        self._log_file = pathlib.Path(value) if isinstance(value, str) else value

    @property
    def log_file_path(self) -> Optional[str]:
        return str(self.log_file.absolute()) if self.log_file else None

    @property
    def banlist(self) -> Optional[pathlib.Path]:
        return self._banlist

    @banlist.setter
    def banlist(self, value: str|pathlib.Path) -> None:
        self._banlist = pathlib.Path(value) if isinstance(value, str) else value

    @property
    def banlist_path(self) -> Optional[str]:
        return str(self.banlist.absolute()) if self.banlist else None

    @property
    def allowlist(self) -> Optional[pathlib.Path]:
        return self._allowlist

    @allowlist.setter
    def allowlist(self, value: str|pathlib.Path) -> None:
        self._allowlist = pathlib.Path(value) if isinstance(value, str) else value

    @property
    def allowlist_path(self) -> Optional[str]:
        return str(self.allowlist.absolute()) if self.allowlist else None

    @property
    def base_url(self) -> str:
        return f"{'https' if self.https else 'http'}://{self.domain}"

    @classmethod
    def from_args(cls, args) -> 'FicheServer':
        fiche = cls()
        fiche.domain = args.domain or fiche.domain
        fiche.port = args.port or fiche.port
        fiche.listen_addr = args.listen_addr or fiche.listen_addr
        fiche.slug_size = args.slug_size or fiche.slug_size
        fiche.https = args.https or fiche.https
        fiche.output_dir = args.output_dir or fiche.output_dir
        fiche.log_file = args.log_file or fiche.log_file
        fiche.banlist = args.banlist or fiche.banlist
        fiche.allowlist = args.allowlist or fiche.allowlist
        fiche.buffer_size = args.buffer_size or fiche.buffer_size

        fiche.logger = logging.getLogger('pyfiche')
        fiche.logger.setLevel(logging.INFO if not args.debug else logging.DEBUG)
        handler = logging.StreamHandler() if not args.log_file else logging.FileHandler(args.log_file)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        fiche.logger.addHandler(handler)

        if args.user_name:
            fiche.logger.fatal("PyFiche does not support switching to a different user. Please run as the appropriate user directly.")

        return fiche

    def get_date(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.listen_addr, self.port))
            s.listen()

            self.logger.info(f"Server started listening on: {self.listen_addr}:{self.port}")

            while True:
                conn, addr = s.accept()
                threading.Thread(target=self.handle_connection, args=(conn, addr,)).start()

    def generate_slug(self, length: Optional[int] = None):
        slug = ''.join(random.choice(self.FICHE_SYMBOLS) for _ in range(length or self.slug_size))

        if self.output_dir:
            while os.path.exists(os.path.join(self.output_dir, slug)):
                slug = ''.join(random.choice(self.FICHE_SYMBOLS) for _ in range(length + extra_length))

        return slug

    def create_directory(self, output_dir, slug):
        path = os.path.join(output_dir, slug)
        try:
            if not os.path.exists(path):
                os.makedirs(path)
            return path
        except Exception as e:
            self.logger.error(f"Error creating directory {path}: {e}")
            return None

    def save_to_file(self, data, slug):
        path = os.path.join(self.output_dir, slug, self.OUTPUT_FILE_NAME)

        os.makedirs(os.path.dirname(path), exist_ok=True)

        try:
            with open(path, 'wb') as file:
                file.write(data)
            return path
        except Exception as e:
            self.logger.error(f"Error saving file {path}: {e}")
            return None

    def handle_connection(self, conn: socket.socket, addr: Tuple[str, int]):
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

        try:
            received_data = bytearray()

            try:
                while True:
                    data = conn.recv(self.buffer_size)
                    self.logger.debug(f"Read {len(data)} bytes from {addr}")
                    if not data:
                        break

                    received_data.extend(data)

            except socket.timeout:
                pass

            data = bytes(received_data)

            self.logger.debug(f"Received {len(data)} bytes in total from {addr}")

            if not data:
                self.logger.error("No data received from the client!")
                return

            slug = self.generate_slug(self.slug_size)
            dir_path = self.create_directory(self.output_dir, slug)
            if dir_path is None:
                return

            file_path = self.save_to_file(data, slug)

            if file_path:
                url = f"{self.base_url}/{slug}\n"
                conn.sendall(url.encode('utf-8'))
                self.logger.info(f"Received {len(data)} bytes, saved to: {slug}")
            else:
                self.logger.error("Failed to save data to file.")

        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
            raise
        finally:
            conn.close()

    def run(self):
        if not self.logger:
            self.logger = logging.getLogger('pyfiche')
            self.logger.setLevel(logging.INFO)
            handler = logging.StreamHandler() if not self.log_file else logging.FileHandler(self.log_file)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)

        if self.banlist and self.allowlist:
            self.logger.fatal("Banlist and allowlist cannot be used together!")
            exit(1)

        if self.banlist_path and not os.path.exists(self.banlist_path):
            self.logger.fatal(f"Banlist file ({self.banlist_path}) does not exist!")
            exit(1)

        if self.allowlist_path and not os.path.exists(self.allowlist_path):
            self.logger.fatal(f"Allowlist file ({self.allowlist_path}) does not exist!")
            exit(1)

        self.logger.info(f"Starting PyFiche...")

        if self.output_dir.exists() and not os.access(self.output_dir_path, os.W_OK):
            self.logger.fatal(f"Output directory ({self.output_dir}) not writable!")
            exit(1)

        elif not self.output_dir.exists():
            try:
                self.output_dir.mkdir(parents=True)
            except Exception as e:
                self.logger.fatal(f"Error creating output directory ({self.output_dir}): {e}")
                exit(1)

        if self.log_file_path:
            try:
                with open(self.log_file_path, 'a'):
                    pass
            except IOError:
                self.logger.fatal("Log file not writable!")
                exit(1)

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