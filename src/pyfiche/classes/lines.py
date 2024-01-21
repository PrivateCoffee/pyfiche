from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from typing import Union, Optional

import logging
import pathlib

from .fiche import FicheServer


class LinesHTTPRequestHandler(BaseHTTPRequestHandler):
    FICHE_SYMBOLS = FicheServer.FICHE_SYMBOLS
    DATA_FILE_NAME = FicheServer.OUTPUT_FILE_NAME

    BASE_HTML = """<!DOCTYPE html>
<html>
<head>
<title>PyFiche Lines</title>
<style>
code {{
    white-space: pre-wrap;
    word-wrap: break-word;
    
    font-family: monospace;
    font-size: 1em;
    font-weight: 400;

    color: #212529;
    background-color: #f8f9fa;
    border-radius: 0.25rem;
    padding: 0.2rem 0.4rem;
    margin: 0.2rem 0;
    display: inline-block;
    overflow: auto;
}}

body {{
    font-family: sans-serif;
    font-size: 1em;
}}
</style>
</head>
<body>
<pre>{content}</pre>
</body>
</html>
"""

    server_version = "PyFiche Lines/dev"

    def not_found(self):
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not found")

    def check_allowlist(self, addr):
        if not self.allowlist:
            return True

        try:
            ip = ipaddress.ip_address(addr)
            with open(self.allowlist, "r") as file:
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
        if not self.banlist:
            return False

        try:
            ip = ipaddress.ip_address(addr)
            with open(self.banlist, "r") as file:
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

    def do_GET(self):
        client_ip, client_port = self.client_address

        self.logger.info(f"GET request from {client_ip}:{client_port}")

        url = urlparse(self.path.rstrip("/"))

        # Discard any URLs that aren't of the form /<slug> or /<slug>/raw
        if not len(url.path.split("/")) in [2, 3]:
            return self.not_found()

        raw = False

        if len(url.path.split("/")) == 3:
            if url.path.split("/")[2] != "raw":
                return self.not_found()
            raw = True
        slug = url.path.split("/")[1]

        # Prevent any invalid characters from being used.
        # This should prevent directory traversal attacks.
        if any([c not in self.FICHE_SYMBOLS for c in slug]):
            return self.not_found()

        file_path = self.data_dir / slug / self.DATA_FILE_NAME

        if not file_path.exists():
            return self.not_found()

        with open(file_path, "rb") as f:
            content = f.read()

            try:
                content.decode("utf-8")
                binary = False
            except UnicodeDecodeError:
                binary = True

            self.send_response(200)

            if raw:
                # Veeeeery basic MIME type detection - TODO?
                self.send_header(
                    "Content-Type",
                    "application/octet-stream" if binary else "text/plain",
                )
                self.send_header("Content-Length", len(content))
                self.send_header(
                    "Content-Disposition",
                    f'attachment; filename="{slug}.{"bin" if binary else "txt"}"',
                )
                self.end_headers()

                self.wfile.write(content)
                return

            if binary:
                content = (
                    f'Binary file - cannot display. <a href="{slug}/raw">Download</a>'
                )
            else:
                content = f'Displaying text file content below. <a href="{slug}/raw">Download</a><br><br><code>{content.decode("utf-8")}</code>'

            full_html = self.BASE_HTML.format(content=content)

            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", len(full_html))
            self.end_headers()

            self.wfile.write(full_html.encode("utf-8"))


def make_lines_handler(data_dir, logger, banlist=None, allowlist=None):
    class CustomHandler(LinesHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            self.data_dir: pathlib.Path = data_dir
            self.logger: logging.Logger = logger
            self.banlist: Optional[pathlib.Path] = banlist
            self.allowlist: Optional[pathlib.Path] = allowlist

            super().__init__(*args, **kwargs)

    return CustomHandler


class LinesServer:
    port: int = 9997
    listen_addr: str = "0.0.0.0"
    _data_dir: pathlib.Path = pathlib.Path("data/")
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
    def from_args(cls, args):
        lines = cls()

        lines.port = args.port or lines.port
        lines.listen_addr = args.listen_addr or lines.listen_addr
        lines.data_dir = args.data_dir or lines.data_dir
        lines.log_file = args.log_file or lines.log_file
        lines.banlist = args.banlist or lines.banlist
        lines.allowlist = args.allowlist or lines.allowlist

        lines.logger = logging.getLogger("pyfiche")
        lines.logger.setLevel(logging.INFO if not args.debug else logging.DEBUG)
        handler = (
            logging.StreamHandler()
            if not args.log_file
            else logging.FileHandler(args.log_file)
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        lines.logger.addHandler(handler)

        return lines

    def run(self):
        handler_class = make_lines_handler(
            self.data_dir, self.logger, self.banlist, self.allowlist
        )

        with HTTPServer((self.listen_addr, self.port), handler_class) as httpd:
            self.logger.info(f"Listening on {self.listen_addr}:{self.port}")
            httpd.serve_forever()
