from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Server:
    """A LibreSpeed-compatible test endpoint."""

    name: str
    base_url: str
    download_path: str = "garbage.php"
    upload_path: str = "empty.php"
    ping_path: str = "empty.php"
    ip_path: str = "getIP.php"


@dataclass(frozen=True)
class Result:
    """Measurements expressed in Mbps and milliseconds."""

    server: str
    download_mbps: float
    upload_mbps: float | None
    latency_ms: float
    jitter_ms: float
    timestamp: str
    public_ip: str | None = None
    isp: str | None = None
    location: str | None = None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)
