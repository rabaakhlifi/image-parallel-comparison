# src/versions/multiprocessing_version.py
from multiprocessing import Pool
from typing import List, Dict
from ..processor import convert_to_grayscale
from ..common import Timer
import os

# Fonction wrapper pour convertir une image (utilisée par multiprocessing.Pool)
def _convert_wrapper(args):
    path, output_dir = args
    # Keep minimal: worker calls convert_to_grayscale
    return convert_to_grayscale(path, output_dir)

# Traite les images en parallèle en utilisant multiprocessing.Pool (processus séparés)
def process_multiprocessing(image_paths: List[str], output_dir: str, n_workers: int = None) -> Dict:
    t = Timer(); t.start()
    with Pool(processes=n_workers) as pool:
        args = [(p, output_dir) for p in image_paths]
        results = pool.map(_convert_wrapper, args)
    total = t.stop()
    # extract per-image elapsed? note: convert_to_grayscale doesn't provide elapsed; we measure in parent
    # For simplicity we mark success and rely on total / avg
    return {"total_time": total, "n_images": len(image_paths), "runs": results, "n_workers": n_workers or os.cpu_count()}
