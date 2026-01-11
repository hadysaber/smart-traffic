import argparse
import json
import sys

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload an image to the backend.")
    parser.add_argument("image", help="Path to local JPEG")
    parser.add_argument("--url", default="http://localhost:5000/api/process_image")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        with open(args.image, "rb") as handle:
            files = {"imageFile": (args.image, handle, "image/jpeg")}
            response = requests.post(args.url, files=files, timeout=20)
            response.raise_for_status()
    except FileNotFoundError:
        print("Image file not found")
        return 1
    except requests.RequestException as exc:
        print(f"Request failed: {exc}")
        return 1

    print(json.dumps(response.json(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
