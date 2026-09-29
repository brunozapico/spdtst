from __future__ import annotations

import json
import os
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen

from .models import Result, Server
from .servers import SSL_CONTEXT, USER_AGENT, endpoint


class MeasurementError(RuntimeError):
    pass


def _read_ping(server: Server) -> float:
    started = time.perf_counter()
    request = Request(endpoint(server, server.ping_path), headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=5, context=SSL_CONTEXT) as response:
        response.read(1)
    return (time.perf_counter() - started) * 1000


def latency_and_jitter(server: Server, samples: int = 6) -> tuple[float, float]:
    values: list[float] = []
    for _ in range(samples):
        try:
            values.append(_read_ping(server))
        except (URLError, OSError, TimeoutError):
            continue
    if len(values) < 2:
        raise MeasurementError("The selected server did not respond to latency probes.")
    return statistics.median(values), statistics.mean(abs(b - a) for a, b in zip(values, values[1:]))


def _transfer(url: str, deadline: float, upload: bool, stop: threading.Event) -> int:
    transferred = 0
    payload = os.urandom(256 * 1024) if upload else None
    while time.perf_counter() < deadline and not stop.is_set():
        try:
            headers = {"User-Agent": USER_AGENT, "Cache-Control": "no-cache"}
            request = Request(url, data=payload, headers=headers, method="POST" if upload else "GET")
            with urlopen(request, timeout=10, context=SSL_CONTEXT) as response:
                while time.perf_counter() < deadline:
                    chunk = response.read(64 * 1024)
                    if not chunk:
                        break
                    transferred += len(payload) if upload else len(chunk)
                if upload:
                    transferred += len(payload)
        except (URLError, OSError, TimeoutError):
            stop.set()
            break
    return transferred


def bandwidth_mbps(server: Server, *, upload: bool, duration: float, workers: int = 4) -> float:
    path = server.upload_path if upload else server.download_path
    url = endpoint(server, path)
    stop = threading.Event()
    started = time.perf_counter()
    deadline = started + duration
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_transfer, url, deadline, upload, stop) for _ in range(workers)]
    elapsed = time.perf_counter() - started
    transferred = sum(future.result() for future in futures)
    if not transferred:
        kind = "upload" if upload else "download"
        raise MeasurementError(f"The selected server did not complete the {kind} test.")
    return (transferred * 8) / elapsed / 1_000_000


def connection_details(server: Server) -> dict[str, str | None]:
    """Read optional connection details from the selected endpoint only."""
    request = Request(
        endpoint(server, server.ip_path) + "&isp=true", headers={"User-Agent": USER_AGENT}
    )
    try:
        with urlopen(request, timeout=5, context=SSL_CONTEXT) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (URLError, OSError, TimeoutError, ValueError):
        return {"public_ip": None, "isp": None, "location": None}

    raw = payload.get("rawIspInfo", {}) if isinstance(payload, dict) else {}
    raw = raw if isinstance(raw, dict) else {}
    processed = payload.get("processedString", "") if isinstance(payload, dict) else ""
    processed_ip, separator, processed_isp = str(processed).partition(" - ")
    ip = raw.get("ip") or raw.get("query") or (processed_ip if separator else None)
    isp = raw.get("org") or raw.get("isp") or (processed_isp if separator else None)
    location = ", ".join(
        str(value) for value in (raw.get("city"), raw.get("region"), raw.get("country")) if value
    )
    return {"public_ip": str(ip) if ip else None, "isp": str(isp) if isp else None,
            "location": location or None}


def run_test(server: Server, *, details: bool, duration: float) -> Result:
    latency, jitter = latency_and_jitter(server)
    download = bandwidth_mbps(server, upload=False, duration=duration)
    upload = bandwidth_mbps(server, upload=True, duration=duration)
    info = connection_details(server) if details else {}
    return Result(
        server=server.name,
        download_mbps=round(download, 2),
        upload_mbps=round(upload, 2),
        latency_ms=round(latency, 2),
        jitter_ms=round(jitter, 2),
        timestamp=datetime.now(timezone.utc).isoformat(),
        **info,
    )
