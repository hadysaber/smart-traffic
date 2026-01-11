import datetime
import logging
import os
from typing import List

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config import (
    CAPTURED_IMAGES_DIR,
    DEFAULT_COUNTS,
    HOST,
    LOGS_DIR,
    MODELS_DIR,
    PORT,
    STATIC_DIR,
)
from cv_hook import count_cars
from ml_model import TrafficMLModel

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

model = TrafficMLModel()

system_state = {
    "last_counts": None,
    "last_timings": None,
    "last_image_path": None,
    "last_update_timestamp": None,
    "last_camera_heartbeat": None,
    "last_lights_heartbeat": None,
}


def ensure_directories() -> None:
    for path in [CAPTURED_IMAGES_DIR, LOGS_DIR, MODELS_DIR, STATIC_DIR]:
        os.makedirs(path, exist_ok=True)


ensure_directories()


def timestamp() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


def _is_recent(heartbeat: datetime.datetime, window_seconds: int = 15) -> bool:
    if not heartbeat:
        return False
    return (datetime.datetime.utcnow() - heartbeat).total_seconds() <= window_seconds


def update_state(counts: List[int], timings: dict, image_path: str = None) -> None:
    system_state["last_counts"] = counts
    system_state["last_timings"] = timings
    system_state["last_image_path"] = image_path
    system_state["last_update_timestamp"] = timestamp()


def status_payload() -> dict:
    counts = system_state["last_counts"] or DEFAULT_COUNTS
    last_timings = system_state["last_timings"]
    last_update = system_state["last_update_timestamp"] or timestamp()
    camera_connected = _is_recent(system_state.get("last_camera_heartbeat"))
    lights_connected = _is_recent(system_state.get("last_lights_heartbeat"))

    return {
        "last_counts": counts,
        "last_timings": last_timings,
        "last_image_path": system_state["last_image_path"],
        "last_update_timestamp": last_update,
        "last_camera_heartbeat": system_state.get("last_camera_heartbeat").isoformat() + "Z"
        if system_state.get("last_camera_heartbeat")
        else None,
        "last_lights_heartbeat": system_state.get("last_lights_heartbeat").isoformat() + "Z"
        if system_state.get("last_lights_heartbeat")
        else None,
        "esp32_camera_connected": camera_connected,
        "esp32_lights_connected": lights_connected,
    }


@app.route("/api/health", methods=["GET"])
def health() -> tuple:
    return jsonify({"status": "ok", "time": timestamp()})


@app.route("/", methods=["GET"])
def dashboard() -> tuple:
    return render_template("dashboard.html")


@app.route("/api/status", methods=["GET"])
def status() -> tuple:
    return jsonify(status_payload())


@app.route("/api/heartbeat/camera", methods=["POST"])
def heartbeat_camera() -> tuple:
    system_state["last_camera_heartbeat"] = datetime.datetime.utcnow()
    return jsonify({"status": "ok", "time": timestamp()})


@app.route("/api/heartbeat/lights", methods=["POST"])
def heartbeat_lights() -> tuple:
    system_state["last_lights_heartbeat"] = datetime.datetime.utcnow()
    return jsonify({"status": "ok", "time": timestamp()})


@app.route("/api/process_image", methods=["POST"])
def process_image() -> tuple:
    if "imageFile" not in request.files:
        return jsonify({"error": "imageFile field is required"}), 400

    file_storage = request.files["imageFile"]
    if file_storage.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file_storage.filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400

    image_name = f"traffic_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
    image_path = os.path.join(CAPTURED_IMAGES_DIR, image_name)
    file_storage.save(image_path)

    counts = count_cars(image_path)
    timings = model.predict_timings(counts)
    update_state(counts, timings, image_path)

    logger.info("Processed image %s counts=%s", image_name, counts)
    return jsonify({"counts": counts, "timings": timings, "image_path": image_path})


@app.route("/api/process_counts", methods=["POST"])
def process_counts() -> tuple:
    data = request.get_json(silent=True) or {}
    counts = data.get("car_counts")

    if not isinstance(counts, list) or len(counts) != 4:
        return jsonify({"error": "car_counts must be a list of four integers"}), 400

    if any((not isinstance(c, int)) or c < 0 for c in counts):
        return jsonify({"error": "car_counts values must be non-negative integers"}), 400

    timings = model.predict_timings(counts)
    update_state(counts, timings)

    logger.info("Processed counts payload %s", counts)
    return jsonify({"counts": counts, "timings": timings})


@app.route("/api/get_timings", methods=["GET"])
def get_timings() -> tuple:
    if system_state["last_timings"]:
        return jsonify(system_state["last_timings"])

    timings = model.predict_timings(DEFAULT_COUNTS)
    update_state(DEFAULT_COUNTS, timings)
    return jsonify(timings)


if __name__ == "__main__":
    ensure_directories()
    logger.info("Starting Smart Traffic backend on %s:%s", HOST, PORT)
    app.run(host=HOST, port=PORT)
