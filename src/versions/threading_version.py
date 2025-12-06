# src/versions/threading_version.py
import threading
from typing import List, Dict
from ..processor import convert_to_grayscale
from ..common import Timer
from queue import Queue, Empty

# Fonction exécutée par chaque thread : récupère une image de la queue et la traite
def worker(in_q: Queue, out_list: List, output_dir: str, lock: threading.Lock):
    while True:
        try:
            path = in_q.get_nowait()
        except Empty:
            return
        t = Timer(); t.start()
        res = convert_to_grayscale(path, output_dir)
        elapsed = t.stop()
        with lock:
            out_list.append({"image": path, "elapsed": elapsed, "success": res.get("success", False)})
        in_q.task_done()

# Traite les images en parallèle en utilisant des threads Python
def process_threading(image_paths: List[str], output_dir: str, n_threads: int = 4) -> Dict:
    from queue import Queue
    q = Queue()
    for p in image_paths:
        q.put(p)
    results = []
    lock = threading.Lock()
    threads = []
    main_timer = Timer(); main_timer.start()
    for _ in range(n_threads):
        t = threading.Thread(target=worker, args=(q, results, output_dir, lock), daemon=True)
        t.start(); threads.append(t)
    q.join()
    total = main_timer.stop()
    return {"total_time": total, "n_images": len(image_paths), "runs": results, "n_threads": n_threads}
