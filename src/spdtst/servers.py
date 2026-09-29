from __future__ import annotations

import json
import ssl
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import truststore

from .models import Server

SERVER_LIST_URL = "https://librespeed.org/backend-servers/servers.php"
USER_AGENT = "spdtst/0.1 (+https://github.com/brunozapico/spdtst)"
SSL_CONTEXT = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


class ServerDiscoveryError(RuntimeError):
    pass


def _request(url: str, *, method: str = "GET", timeout: float = 5.0) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT}, method=method)
    with urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
        return response.read()


def _with_scheme(value: str) -> str:
    return value if value.startswith(("https://", "http://")) else f"https:{value}"


def discover_servers(list_url: str = SERVER_LIST_URL) -> list[Server]:
    """Load LibreSpeed's public directory without bundling its server data."""
    try:
        payload = json.loads(_request(list_url, timeout=10).decode("utf-8"))
    except (URLError, TimeoutError, ValueError) as error:
        raise ServerDiscoveryError(
            "Could not load the public server directory. Use --server to provide an endpoint."
        ) from error

    servers: list[Server] = []
    for entry in payload:
        try:
            servers.append(
                Server(
                    name=str(entry["name"]),
                    base_url=_with_scheme(str(entry["server"])),
                    download_path=str(entry.get("dlURL", "garbage.php")),
                    upload_path=str(entry.get("ulURL", "empty.php")),
                    ping_path=str(entry.get("pingURL", "empty.php")),
                    ip_path=str(entry.get("getIpURL", "getIP.php")),
                )
            )
        except (KeyError, TypeError):
            continue
    if not servers:
        raise ServerDiscoveryError("The public server directory did not contain usable servers.")
    return servers


def custom_server(endpoint: str) -> Server:
    """Create a server using LibreSpeed's conventional backend paths."""
    base_url = endpoint.rstrip("/") + "/"
    return Server(name=base_url, base_url=base_url)


def endpoint(server: Server, path: str, cache_buster: bool = True) -> str:
    url = urljoin(server.base_url.rstrip("/") + "/", path.lstrip("/"))
    return f"{url}?r={time.time_ns()}" if cache_buster else url


def _latency(server: Server) -> tuple[Server, float]:
    started = time.perf_counter()
    _request(endpoint(server, server.ping_path), timeout=3)
    return server, (time.perf_counter() - started) * 1000


def select_fastest(servers: list[Server]) -> Server:
    """Probe the public directory in parallel and select the lowest-latency server."""
    sample = servers
    timings: list[tuple[Server, float]] = []
    with ThreadPoolExecutor(max_workers=min(12, len(sample))) as pool:
        futures = [pool.submit(_latency, server) for server in sample]
        for future in as_completed(futures):
            try:
                timings.append(future.result())
            except (URLError, OSError, TimeoutError):
                pass
    if not timings:
        raise ServerDiscoveryError("No discovered test server responded. Try --server <URL>.")
    return min(timings, key=lambda item: item[1])[0]
