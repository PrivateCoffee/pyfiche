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

    INDEX_CONTENT = BASE_HTML.format(
        content="""<h1>PyFiche Lines</h1>
<p>Welcome to PyFiche Lines, a HTTP server for PyFiche.</p>
<p>PyFiche Lines is a HTTP server for PyFiche. It allows you to view files uploaded through PyFiche in your browser.</p>
<p>For more information, see <a href="https://kumig.it/PrivateCoffee/pyfiche">the PyFiche Git repo</a>.</p>"""
    )

    server_version = "PyFiche Lines/dev"

    def do_POST(self):
        client_ip, client_port = self.client_address

        self.logger.info(f"POST request from {client_ip}:{client_port}")

        if (not self.check_allowlist(client_ip)) or self.check_banlist(client_ip):
            self.logger.info(f"Rejected request from {client_ip}:{client_port}")
            return self.not_found()

        # Reject any POST requests that aren't to /

        url = urlparse(self.path.rstrip("/"))

        if url.path != "/":
            return self.not_found()

        # Reject any POST requests that don't have a Content-Length header

        if "Content-Length" not in self.headers:
            return self.invalid_request()

        if not self.headers["Content-Length"].isdigit():
            return self.invalid_request()

        if int(self.headers["Content-Length"]) > self.max_size:
            return self.file_too_large()

        # Upload the file

        content_length = int(self.headers["Content-Length"])
        content = self.rfile.read(content_length)

        if not content:
            return self.not_found()

        slug = FicheServer.generate_slug(self.data_dir, self.FICHE_SYMBOLS)

        file_path = self.data_dir / slug / self.DATA_FILE_NAME

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with file_path.open("wb") as f:
            f.write(content)

        # Redirect the user to the new file

        self.send_response(303)
        self.send_header("Location", f"/{slug}")
        self.end_headers()

    def invalid_request(self):
        self.send_response(400)
        self.end_headers()
        self.wfile.write(b"Invalid request")

    def file_too_large(self):
        self.send_response(413)
        self.end_headers()
        self.wfile.write(b"File too large")

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

        if (not self.check_allowlist(client_ip)) or self.check_banlist(client_ip):
            self.logger.info(f"Rejected request from {client_ip}:{client_port}")
            return self.not_found()

        self.logger.info(f"GET request from {client_ip}:{client_port}")

        url = urlparse(self.path.rstrip("/"))

        # If the URL is /, display the index page
        if url.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", len(self.INDEX_CONTENT))
            self.end_headers()

            self.wfile.write(self.INDEX_CONTENT.encode("utf-8"))
            return

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


def make_lines_handler(
    data_dir, logger, banlist=None, allowlist=None, max_size=5242880
):
    class CustomHandler(LinesHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            self.data_dir: pathlib.Path = data_dir
            self.logger: logging.Logger = logger
            self.banlist: Optional[pathlib.Path] = banlist
            self.allowlist: Optional[pathlib.Path] = allowlist
            self.max_size: int = max_size

            super().__init__(*args, **kwargs)

    return CustomHandler


class LinesServer:
    port: int = 9997
    listen_addr: str = "0.0.0.0"
    max_size: int = 5242880  # 5 MB by default
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
        lines.max_size = args.max_size or lines.max_size
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
            self.data_dir, self.logger, self.banlist, self.allowlist, self.max_size
        )

        with HTTPServer((self.listen_addr, self.port), handler_class) as httpd:
            self.logger.info(f"Listening on {self.listen_addr}:{self.port}")
            httpd.serve_forever()
