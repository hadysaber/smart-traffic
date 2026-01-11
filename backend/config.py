import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAPTURED_IMAGES_DIR = os.path.join(BASE_DIR, "captured_images")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
MODELS_DIR = os.path.join(BASE_DIR, "models")
STATIC_DIR = os.path.join(BASE_DIR, "static")

DEFAULT_COUNTS = [5, 5, 5, 5]

HOST = "0.0.0.0"
PORT = 5000
