# src/runner.py
import argparse
from pathlib import Path
from .common import ensure_dirs, list_images
from .measure import measure_run, export_results
from .versions import mono, threading_version, multiprocessing_version, threadpool_executor, processpool_executor
import os
import json

# Lance toutes les expériences de parallélisme et sauvegarde les résultats
def run_all(images_dir: str, output_dir: str, results_dir: str, sizes: dict):
    ensure_dirs(output_dir, results_dir)
    image_paths = list_images(images_dir)
    if not image_paths:
        raise SystemExit(f"Aucune image trouvée dans {images_dir}. Ajoute des images puis relance.")
    experiments = []

    # 1: Mono
    print("Running mono (séquentiel)...")
    out_mono = output_dir + "/mono"
    os.makedirs(out_mono, exist_ok=True)
    mono_result = measure_run(mono.process_sequential, image_paths, out_mono)
    export_results(results_dir, "mono", mono_result)
    experiments.append(("mono", mono_result))

    # 2: Threading
    for n in sizes.get("threads", [4]):
        print(f"Running threading ({n} threads)...")
        out_thread = output_dir + f"/threading_{n}"
        os.makedirs(out_thread, exist_ok=True)
        thr_res = measure_run(threading_version.process_threading, image_paths, out_thread, n_threads=n)
        export_results(results_dir, f"threading_{n}", thr_res)
        experiments.append((f"threading_{n}", thr_res))

    # 3: Multiprocessing
    for n in sizes.get("processes", [os.cpu_count() or 2]):
        print(f"Running multiprocessing ({n} workers)...")
        out_mp = output_dir + f"/multiproc_{n}"
        os.makedirs(out_mp, exist_ok=True)
        mp_res = measure_run(multiprocessing_version.process_multiprocessing, image_paths, out_mp, n_workers=n)
        export_results(results_dir, f"multiprocessing_{n}", mp_res)
        experiments.append((f"multiprocessing_{n}", mp_res))

    # 4: ThreadPoolExecutor
    for n in sizes.get("threads", [4]):
        print(f"Running ThreadPoolExecutor ({n})...")
        out_tpe = output_dir + f"/threadpool_{n}"
        os.makedirs(out_tpe, exist_ok=True)
        tpe_res = measure_run(threadpool_executor.process_threadpool, image_paths, out_tpe, max_workers=n)
        export_results(results_dir, f"threadpool_{n}", tpe_res)
        experiments.append((f"threadpool_{n}", tpe_res))

    # 5: ProcessPoolExecutor
    for n in sizes.get("processes", [os.cpu_count() or 2]):
        print(f"Running ProcessPoolExecutor ({n})...")
        out_ppe = output_dir + f"/processpool_{n}"
        os.makedirs(out_ppe, exist_ok=True)
        ppe_res = measure_run(processpool_executor.process_processpool, image_paths, out_ppe, max_workers=n)
        export_results(results_dir, f"processpool_{n}", ppe_res)
        experiments.append((f"processpool_{n}", ppe_res))

    # Summary
    summary = {
        "n_images": len(image_paths),
        "experiments": [
            {
                "name": name,
                "total_time": data["total_time"],
                "avg_time_per_image": data["avg_time_per_image"],
                "throughput_img_per_sec": data["throughput_img_per_sec"]
            } for (name, data) in experiments
        ]
    }
    with open(os.path.join(results_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print("All done. Results saved to:", results_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare different parallel models for image grayscale conversion.")
    parser.add_argument("--images", default="../images", help="Folder with images")
    parser.add_argument("--output", default="../output", help="Folder for output images")
    parser.add_argument("--results", default="../results", help="Folder for results")
    parser.add_argument("--threads", nargs="+", type=int, default=[2,4,8], help="Thread counts to test")
    parser.add_argument("--processes", nargs="+", type=int, default=[2,4], help="Process counts to test")
    args = parser.parse_args()
    sizes = {"threads": args.threads, "processes": args.processes}
    run_all(args.images, args.output, args.results, sizes)
