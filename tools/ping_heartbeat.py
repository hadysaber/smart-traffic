import argparse
import sys

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ping heartbeat endpoints.")
    parser.add_argument(
        "--camera",
        default="http://localhost:5000/api/heartbeat/camera",
        help="Camera heartbeat URL",
    )
    parser.add_argument(
        "--lights",
        default="http://localhost:5000/api/heartbeat/lights",
        help="Lights heartbeat URL",
    )
    parser.add_argument("--target", choices=["camera", "lights", "both"], default="both")
    return parser.parse_args()


def post(url: str) -> None:
    response = requests.post(url, timeout=5)
    response.raise_for_status()
    print(f"OK: {url} -> {response.json()}")


def main() -> int:
    args = parse_args()
    try:
        if args.target in ("camera", "both"):
            post(args.camera)
        if args.target in ("lights", "both"):
            post(args.lights)
    except requests.RequestException as exc:
        print(f"Heartbeat failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
