from dataclasses import dataclass
from typing import Dict, List

MIN_GREEN = 20
MAX_GREEN = 60
YELLOW_TIME = 3
ALL_RED_TIME = 2


@dataclass
class TimingPrediction:
    ns_green: int
    ew_green: int
    yellow_time: int
    all_red_time: int
    total_cycle: int


class TrafficMLModel:
    """Heuristic timing model for smart traffic lights."""

    def predict_timings(self, counts: List[int]) -> Dict[str, Dict]:
        if len(counts) != 4 or any(c < 0 for c in counts):
            raise ValueError("counts must be a list of four non-negative integers")

        north, east, south, west = counts
        ns_total = north + south
        ew_total = east + west
        ratio = (ns_total / max(ew_total, 1)) if ew_total > 0 else float("inf")

        ns_green, ew_green = self._base_green_times(ratio)

        if ew_total > ns_total:
            ns_green, ew_green = ew_green, ns_green

        ns_green = self._clamp(ns_green)
        ew_green = self._clamp(ew_green)

        total_cycle = ns_green + ew_green + (YELLOW_TIME * 2) + (ALL_RED_TIME * 2)
        predictions = TimingPrediction(
            ns_green=ns_green,
            ew_green=ew_green,
            yellow_time=YELLOW_TIME,
            all_red_time=ALL_RED_TIME,
            total_cycle=total_cycle,
        )

        return {
            "predictions": predictions.__dict__,
            "commands": self._build_commands(predictions),
            "analysis": {
                "pattern": self._pattern_label(ns_total, ew_total),
                "counts": counts,
                "ns_total": ns_total,
                "ew_total": ew_total,
                "ratio": round(ratio if ratio != float("inf") else 999.0, 2),
            },
        }

    def _base_green_times(self, ratio: float) -> (int, int):
        if ratio >= 3:
            return 55, 20
        if ratio >= 2:
            return 48, 25
        if ratio >= 1.5:
            return 42, 30
        return 35, 35

    def _clamp(self, value: int) -> int:
        return max(MIN_GREEN, min(MAX_GREEN, int(round(value))))

    def _pattern_label(self, ns_total: int, ew_total: int) -> str:
        if ns_total == ew_total:
            return "balanced"
        return "ns_heavy" if ns_total > ew_total else "ew_heavy"

    def _build_commands(self, predictions: TimingPrediction) -> Dict[str, Dict]:
        return {
            "phase1": {
                "ns": "GREEN",
                "ew": "RED",
                "duration": predictions.ns_green,
                "description": "North/South green phase",
            },
            "phase2": {
                "ns": "YELLOW",
                "ew": "RED",
                "duration": predictions.yellow_time,
                "description": "North/South yellow clearance",
            },
            "phase3": {
                "all": "RED",
                "duration": predictions.all_red_time,
                "description": "All-red buffer",
            },
            "phase4": {
                "ns": "RED",
                "ew": "GREEN",
                "duration": predictions.ew_green,
                "description": "East/West green phase",
            },
            "phase5": {
                "ns": "RED",
                "ew": "YELLOW",
                "duration": predictions.yellow_time,
                "description": "East/West yellow clearance",
            },
            "phase6": {
                "all": "RED",
                "duration": predictions.all_red_time,
                "description": "All-red buffer",
            },
        }


if __name__ == "__main__":
    model = TrafficMLModel()
    sample = model.predict_timings([12, 4, 11, 3])
    print("Sample timing prediction:")
    print(sample)
