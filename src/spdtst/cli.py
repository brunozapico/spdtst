from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .measure import MeasurementError, run_test
from .servers import ServerDiscoveryError, custom_server, discover_servers, select_fastest
from .storage import save


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spdtst", description="A small, private-by-default internet speed test."
    )
    parser.add_argument("--version", action="version", version=f"spdtst {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, details, help_text in (
        ("test", False, "Measure download, upload, latency, and jitter."),
        ("test_full", True, "Run the network test plus IP, ISP, and approximate location lookup."),
        ("test-full", True, "Alias for test_full."),
    ):
        command = commands.add_parser(name, help=help_text)
        command.set_defaults(details=details)
        command.add_argument("--server", metavar="URL", help="A LibreSpeed-compatible backend URL.")
        command.add_argument("--duration", type=float, default=5, help="Seconds per transfer test (default: 5).")
        command.add_argument("--save", action="store_true", help="Append the result to the local history file.")
        command.add_argument("--output", choices=("human", "json"), default="human", help="Result format.")
        command.add_argument("--save-to", metavar="PATH", type=Path, help="Write history to this JSONL file (implies --save).")
    return parser


def _print_result(result, output: str, show_details: bool) -> None:
    if output == "json":
        print(json.dumps(result.as_dict(), indent=2))
        return
    print(f"\nServer     {result.server}")
    print(f"Download   {result.download_mbps:.2f} Mbps")
    print(f"Upload     {result.upload_mbps:.2f} Mbps")
    print(f"Latency    {result.latency_ms:.2f} ms")
    print(f"Jitter     {result.jitter_ms:.2f} ms")
    if show_details:
        print(f"Public IP  {result.public_ip or 'Unavailable'}")
        print(f"ISP        {result.isp or 'Unavailable'}")
        print(f"Location   {result.location or 'Unavailable'}")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.duration <= 0:
        print("error: --duration must be greater than zero", file=sys.stderr)
        return 2
    try:
        if args.server:
            server = custom_server(args.server)
        else:
            print("Finding the nearest available server…")
            server = select_fastest(discover_servers())
        print(f"Testing with {server.name}…")
        result = run_test(server, details=args.details, duration=args.duration)
    except (ServerDiscoveryError, MeasurementError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    _print_result(result, args.output, args.details)
    if args.save or args.save_to:
        location = save(result, args.save_to)
        if args.output == "human":
            print(f"Saved to {location}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
