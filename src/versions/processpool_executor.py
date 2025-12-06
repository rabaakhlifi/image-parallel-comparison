# src/versions/processpool_executor.py
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict
from ..processor import convert_to_grayscale
from ..common import Timer

# Fonction wrapper pour convertir une image (utilisée par ProcessPoolExecutor)
def _wrapper(p_out):
    path, output_dir = p_out
    return convert_to_grayscale(path, output_dir)

# Traite les images en parallèle en utilisant ProcessPoolExecutor (processus séparés)
def process_processpool(image_paths: List[str], output_dir: str, max_workers: int = None) -> Dict:
    timer = Timer(); timer.start()
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_wrapper, (p, output_dir)): p for p in image_paths}
        for fut in as_completed(futures):
            results.append(fut.result())
    total = timer.stop()
    return {"total_time": total, "n_images": len(image_paths), "runs": results, "max_workers": max_workers}
