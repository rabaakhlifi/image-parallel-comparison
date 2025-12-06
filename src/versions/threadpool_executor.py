# src/versions/threadpool_executor.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
from ..processor import convert_to_grayscale
from ..common import Timer

# Traite les images en parallèle en utilisant ThreadPoolExecutor (threads)
def process_threadpool(image_paths: List[str], output_dir: str, max_workers: int = None) -> Dict:
    timer = Timer(); timer.start()
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(convert_to_grayscale, p, output_dir): p for p in image_paths}
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
    total = timer.stop()
    return {"total_time": total, "n_images": len(image_paths), "runs": results, "max_workers": max_workers}
