# src/measure.py
import time
import psutil
from typing import Callable, List, Dict, Any
from .common import save_results_json, save_results_csv, ensure_dirs, safe_filename
import os
from statistics import mean

# Mesure les performances d'exécution d'une fonction (temps total, temps moyen, débit)
def measure_run(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Mesure le temps total, temps moyen par image, débit (img/s) et optional CPU usage sample.
    func doit retourner dictionnaire contenant 'total_time' et 'n_images' et 'runs' list optionally.
    """
    # CPU sampling (optional) if psutil installed
    cpu_samples = []
    sampling = kwargs.pop("cpu_sampling", False)
    sample_interval = kwargs.pop("sample_interval", 0.05)
    if sampling and psutil:
        _stop = False
        def _sample():
            while not _stop:
                cpu_samples.append(psutil.cpu_percent(interval=None))
                time.sleep(sample_interval)
        import threading
        samp_thread = threading.Thread(target=_sample, daemon=True)
        samp_thread.start()
    t0 = time.perf_counter()
    res = func(*args, **kwargs)
    total = time.perf_counter() - t0
    if sampling and psutil:
        _stop = True
        # small delay to let thread stop
        time.sleep(sample_interval*1.1)
    n = res.get("n_images", len(res.get("runs", [])))
    avg = total / n if n else None
    throughput = n / total if total and n else None
    return {
        "total_time": total,
        "n_images": n,
        "avg_time_per_image": avg,
        "throughput_img_per_sec": throughput,
        "cpu_samples": cpu_samples,
        "raw_result": res
    }

# Exporte les résultats de mesure au format JSON et CSV
def export_results(base_path: str, name: str, data: Dict):
    os.makedirs(base_path, exist_ok=True)
    # json
    save_results_json(os.path.join(base_path, f"{name}.json"), data)
    # csv summary
    headers = ["metric", "value"]
    rows = [
        ["total_time", data["total_time"]],
        ["n_images", data["n_images"]],
        ["avg_time_per_image", data["avg_time_per_image"]],
        ["throughput_img_per_sec", data["throughput_img_per_sec"]],
        ["cpu_sample_mean", (sum(data["cpu_samples"])/len(data["cpu_samples"])) if data["cpu_samples"] else None]
    ]
    save_results_csv(os.path.join(base_path, f"{name}_summary.csv"), headers, rows)
