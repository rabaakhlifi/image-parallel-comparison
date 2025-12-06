# src/versions/mono.py
from typing import List, Dict
from pathlib import Path
from ..processor import convert_to_grayscale
from ..common import Timer

# Traite les images de manière séquentielle (une par une, sans parallélisme)
def process_sequential(image_paths: List[str], output_dir: str) -> Dict:
    timer = Timer()
    stats = {"runs": []}
    timer.start()
    for p in image_paths:
        t = Timer(); t.start()
        res = convert_to_grayscale(p, output_dir)
        elapsed = t.stop()
        stats["runs"].append({"image": p, "elapsed": elapsed, "success": res.get("success", False)})
    total = timer.stop()
    stats.update({"total_time": total, "n_images": len(image_paths)})
    return stats
