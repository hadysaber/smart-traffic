import hashlib
import os


def count_cars(image_path):
    """Return deterministic simulated counts based on image filename hash."""
    filename = os.path.basename(image_path)
    digest = hashlib.sha256(filename.encode("utf-8")).hexdigest()
    counts = []
    for idx in range(0, 16, 4):
        value = int(digest[idx:idx + 4], 16)
        counts.append(value % 21)
    return counts
