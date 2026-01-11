import argparse
import json
import sys

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send car counts to backend.")
    parser.add_argument("--url", default="http://localhost:5000/api/process_counts")
    parser.add_argument("counts", nargs=4, type=int, help="Counts for N E S W")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = {"car_counts": args.counts}

    try:
        response = requests.post(args.url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Request failed: {exc}")
        return 1

    print(json.dumps(response.json(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
