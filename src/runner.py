# src/runner.py
"""
Orchestrateur principal pour exécuter toutes les expériences de parallélisme.
Compare les différentes approches avec et sans synchronisation.

Ce module est le point d'entrée principal du projet. Il orchestre l'exécution
de toutes les expériences de comparaison des approches de parallélisme et
génère un résumé comparatif des résultats.

Rôle détaillé :
- Lance toutes les expériences (mono, threading, multiprocessing, etc.)
- Compare les versions avec et sans synchronisation
- Mesure les performances de chaque approche
- Collecte les métriques de synchronisation
- Génère un résumé comparatif au format JSON
- Gère les arguments en ligne de commande
"""
import argparse  # Module pour parser les arguments en ligne de commande
from pathlib import Path  # Import de Path (non utilisé directement mais gardé pour cohérence)
from .common import ensure_dirs, list_images  # Import des fonctions utilitaires (création dossiers, liste images)
from .measure import measure_run, export_results  # Import des fonctions de mesure et d'export
from .versions import (  # Import de tous les modules de versions
    mono,  # Version séquentielle (baseline)
    threading_version,  # Version avec threading
    multiprocessing_version,  # Version avec multiprocessing
    threadpool_executor,  # Version avec ThreadPoolExecutor
    processpool_executor  # Version avec ProcessPoolExecutor
)
import os  # Module pour les opérations sur le système de fichiers
import json  # Module pour la sérialisation/désérialisation JSON


# Lance toutes les expériences de parallélisme et sauvegarde les résultats
def run_all(images_dir: str, output_dir: str, results_dir: str, sizes: dict):
    """
    Lance toutes les expériences de comparaison des approches de parallélisme.
    
    Expériences exécutées :
    1. Mono-thread (baseline séquentielle)
    2. Threading sans lock (race condition)
    3. Threading avec lock (correction)
    4. Threading avec semaphore
    5. Multiprocessing avec lock
    6. ThreadPoolExecutor avec lock
    7. ThreadPoolExecutor avec semaphore
    8. ProcessPoolExecutor avec lock
    
    Args:
        images_dir: Dossier contenant les images
        output_dir: Dossier pour les images converties
        results_dir: Dossier pour les résultats de performance
        sizes: Dictionnaire avec les nombres de threads/processus à tester
    """
    ensure_dirs(output_dir, results_dir)  # Crée les dossiers de sortie et résultats s'ils n'existent pas
    image_paths = list_images(images_dir)  # Liste tous les fichiers images dans le dossier
    
    if not image_paths:  # Vérifie s'il y a des images
        raise SystemExit(f"Aucune image trouvée dans {images_dir}. Ajoute des images puis relance.")  # Arrête le programme avec un message d'erreur
    
    experiments = []  # Liste pour stocker tous les résultats d'expériences
    
    # 1: Mono-thread (baseline)
    print("=" * 60)  # Affiche une ligne de séparation
    print("Running mono (séquentiel - baseline)...")  # Affiche le message de démarrage
    print("=" * 60)  # Affiche une ligne de séparation
    out_mono = os.path.join(output_dir, "mono")  # Construit le chemin du dossier de sortie pour mono
    os.makedirs(out_mono, exist_ok=True)  # Crée le dossier de sortie s'il n'existe pas
    mono_result = measure_run(mono.process_sequential, image_paths, out_mono)  # Exécute et mesure la version séquentielle
    export_results(results_dir, "mono", mono_result)  # Exporte les résultats au format JSON et CSV
    experiments.append(("mono", mono_result))  # Ajoute les résultats à la liste d'expériences
    
    # 2: Threading SANS lock (race condition)
    for n in sizes.get("threads", [4]):  # Parcourt chaque nombre de threads à tester
        print("=" * 60)  # Affiche une ligne de séparation
        print(f"Running threading ({n} threads) SANS LOCK (race condition)...")  # Affiche le message avec le nombre de threads
        print("=" * 60)  # Affiche une ligne de séparation
        out_thread = os.path.join(output_dir, f"threading_{n}_no_lock")  # Construit le chemin du dossier de sortie
        os.makedirs(out_thread, exist_ok=True)  # Crée le dossier de sortie s'il n'existe pas
        thr_res = measure_run(  # Exécute et mesure la version threading sans lock
            threading_version.process_threading,  # Fonction à exécuter
            image_paths,  # Liste des images à traiter
            out_thread,  # Dossier de sortie
            n_threads=n,  # Nombre de threads
            use_lock=False  # Désactive la protection par lock (race condition)
        )
        export_results(results_dir, f"threading_{n}_no_lock", thr_res)  # Exporte les résultats
        experiments.append((f"threading_{n}_no_lock", thr_res))  # Ajoute les résultats à la liste
    
    # 3: Threading AVEC lock (correction)
    for n in sizes.get("threads", [4]):  # Parcourt chaque nombre de threads à tester
        print("=" * 60)  # Affiche une ligne de séparation
        print(f"Running threading ({n} threads) AVEC LOCK (mutex)...")  # Affiche le message avec le nombre de threads
        print("=" * 60)  # Affiche une ligne de séparation
        out_thread = os.path.join(output_dir, f"threading_{n}_with_lock")  # Construit le chemin du dossier de sortie
        os.makedirs(out_thread, exist_ok=True)  # Crée le dossier de sortie s'il n'existe pas
        thr_res = measure_run(  # Exécute et mesure la version threading avec lock
            threading_version.process_threading,  # Fonction à exécuter
            image_paths,  # Liste des images à traiter
            out_thread,  # Dossier de sortie
            n_threads=n,  # Nombre de threads
            use_lock=True  # Active la protection par lock (correction des race conditions)
        )
        export_results(results_dir, f"threading_{n}_with_lock", thr_res)  # Exporte les résultats
        experiments.append((f"threading_{n}_with_lock", thr_res))  # Ajoute les résultats à la liste
    
    # 4: Threading AVEC semaphore
    for n in sizes.get("threads", [4]):  # Parcourt chaque nombre de threads à tester
        print("=" * 60)  # Affiche une ligne de séparation
        print(f"Running threading ({n} threads) AVEC SEMAPHORE...")  # Affiche le message avec le nombre de threads
        print("=" * 60)  # Affiche une ligne de séparation
        out_thread = os.path.join(output_dir, f"threading_{n}_semaphore")  # Construit le chemin du dossier de sortie
        os.makedirs(out_thread, exist_ok=True)  # Crée le dossier de sortie s'il n'existe pas
        thr_res = measure_run(  # Exécute et mesure la version threading avec semaphore
            threading_version.process_threading,  # Fonction à exécuter
            image_paths,  # Liste des images à traiter
            out_thread,  # Dossier de sortie
            n_threads=n,  # Nombre de threads
            use_lock=False,  # Désactive le lock (on utilise le semaphore)
            use_semaphore=True,  # Active le semaphore pour limiter l'accès concurrent
            max_concurrent_log=2  # Nombre maximum de threads pouvant écrire simultanément
        )
        export_results(results_dir, f"threading_{n}_semaphore", thr_res)  # Exporte les résultats
        experiments.append((f"threading_{n}_semaphore", thr_res))  # Ajoute les résultats à la liste
    
    # 5: Multiprocessing AVEC lock
    for n in sizes.get("processes", [os.cpu_count() or 2]):  # Parcourt chaque nombre de processus à tester (défaut: nombre de CPU)
        print("=" * 60)  # Affiche une ligne de séparation
        print(f"Running multiprocessing ({n} workers) AVEC LOCK...")  # Affiche le message avec le nombre de processus
        print("=" * 60)  # Affiche une ligne de séparation
        out_mp = os.path.join(output_dir, f"multiproc_{n}_with_lock")  # Construit le chemin du dossier de sortie
        os.makedirs(out_mp, exist_ok=True)  # Crée le dossier de sortie s'il n'existe pas
        mp_res = measure_run(  # Exécute et mesure la version multiprocessing avec lock
            multiprocessing_version.process_multiprocessing,  # Fonction à exécuter
            image_paths,  # Liste des images à traiter
            out_mp,  # Dossier de sortie
            n_workers=n,  # Nombre de processus workers
            use_lock=True  # Active la protection par lock multiprocessing
        )
        export_results(results_dir, f"multiprocessing_{n}_with_lock", mp_res)  # Exporte les résultats
        experiments.append((f"multiprocessing_{n}_with_lock", mp_res))  # Ajoute les résultats à la liste
    
    # 6: ThreadPoolExecutor AVEC lock
    for n in sizes.get("threads", [4]):  # Parcourt chaque nombre de threads à tester
        print("=" * 60)  # Affiche une ligne de séparation
        print(f"Running ThreadPoolExecutor ({n} workers) AVEC LOCK...")  # Affiche le message avec le nombre de workers
        print("=" * 60)  # Affiche une ligne de séparation
        out_tpe = os.path.join(output_dir, f"threadpool_{n}_with_lock")  # Construit le chemin du dossier de sortie
        os.makedirs(out_tpe, exist_ok=True)  # Crée le dossier de sortie s'il n'existe pas
        tpe_res = measure_run(  # Exécute et mesure la version ThreadPoolExecutor avec lock
            threadpool_executor.process_threadpool,  # Fonction à exécuter
            image_paths,  # Liste des images à traiter
            out_tpe,  # Dossier de sortie
            max_workers=n,  # Nombre maximum de threads workers
            use_lock=True  # Active la protection par lock
        )
        export_results(results_dir, f"threadpool_{n}_with_lock", tpe_res)  # Exporte les résultats
        experiments.append((f"threadpool_{n}_with_lock", tpe_res))  # Ajoute les résultats à la liste
    
    # 7: ThreadPoolExecutor AVEC semaphore
    for n in sizes.get("threads", [4]):  # Parcourt chaque nombre de threads à tester
        print("=" * 60)  # Affiche une ligne de séparation
        print(f"Running ThreadPoolExecutor ({n} workers) AVEC SEMAPHORE...")  # Affiche le message avec le nombre de workers
        print("=" * 60)  # Affiche une ligne de séparation
        out_tpe = os.path.join(output_dir, f"threadpool_{n}_semaphore")  # Construit le chemin du dossier de sortie
        os.makedirs(out_tpe, exist_ok=True)  # Crée le dossier de sortie s'il n'existe pas
        tpe_res = measure_run(  # Exécute et mesure la version ThreadPoolExecutor avec semaphore
            threadpool_executor.process_threadpool,  # Fonction à exécuter
            image_paths,  # Liste des images à traiter
            out_tpe,  # Dossier de sortie
            max_workers=n,  # Nombre maximum de threads workers
            use_lock=False,  # Désactive le lock (on utilise le semaphore)
            use_semaphore=True,  # Active le semaphore pour limiter l'accès concurrent
            max_concurrent_log=2  # Nombre maximum de threads pouvant écrire simultanément
        )
        export_results(results_dir, f"threadpool_{n}_semaphore", tpe_res)  # Exporte les résultats
        experiments.append((f"threadpool_{n}_semaphore", tpe_res))  # Ajoute les résultats à la liste
    
    # 8: ProcessPoolExecutor AVEC lock
    for n in sizes.get("processes", [os.cpu_count() or 2]):  # Parcourt chaque nombre de processus à tester (défaut: nombre de CPU)
        print("=" * 60)  # Affiche une ligne de séparation
        print(f"Running ProcessPoolExecutor ({n} workers) AVEC LOCK...")  # Affiche le message avec le nombre de workers
        print("=" * 60)  # Affiche une ligne de séparation
        out_ppe = os.path.join(output_dir, f"processpool_{n}_with_lock")  # Construit le chemin du dossier de sortie
        os.makedirs(out_ppe, exist_ok=True)  # Crée le dossier de sortie s'il n'existe pas
        ppe_res = measure_run(  # Exécute et mesure la version ProcessPoolExecutor avec lock
            processpool_executor.process_processpool,  # Fonction à exécuter
            image_paths,  # Liste des images à traiter
            out_ppe,  # Dossier de sortie
            max_workers=n,  # Nombre maximum de processus workers
            use_lock=True  # Active la protection par lock multiprocessing
        )
        export_results(results_dir, f"processpool_{n}_with_lock", ppe_res)  # Exporte les résultats
        experiments.append((f"processpool_{n}_with_lock", ppe_res))  # Ajoute les résultats à la liste
    
    # Résumé comparatif
    print("=" * 60)  # Affiche une ligne de séparation
    print("Génération du résumé comparatif...")  # Affiche le message de génération du résumé
    print("=" * 60)  # Affiche une ligne de séparation
    
    summary = {  # Crée le dictionnaire de résumé
        "n_images": len(image_paths),  # Nombre total d'images traitées
        "experiments": []  # Liste vide pour stocker les données de chaque expérience
    }
    
    for name, data in experiments:  # Parcourt toutes les expériences exécutées
        sync_metrics = data.get("sync_metrics", {})  # Récupère les métriques de synchronisation
        exp_data = {  # Crée un dictionnaire avec les données de cette expérience
            "name": name,  # Nom de l'expérience
            "total_time": data["total_time"],  # Temps total d'exécution
            "avg_time_per_image": data["avg_time_per_image"],  # Temps moyen par image
            "throughput_img_per_sec": data["throughput_img_per_sec"],  # Débit en images/seconde
            "sync_total_wait_time": sync_metrics.get("total_wait_time", 0),  # Temps total d'attente sur verrous/sémaphores
            "sync_lock_wait_time": sync_metrics.get("total_lock_wait_time", 0),  # Temps total d'attente sur verrous
            "sync_semaphore_wait_time": sync_metrics.get("total_semaphore_wait_time", 0),  # Temps total d'attente sur sémaphores
            "sync_contention_count": sync_metrics.get("contention_count", 0)  # Nombre de contentions
        }
        summary["experiments"].append(exp_data)  # Ajoute les données de cette expérience au résumé
    
    summary_path = os.path.join(results_dir, "summary.json")  # Construit le chemin du fichier de résumé
    with open(summary_path, "w", encoding="utf-8") as f:  # Ouvre le fichier en mode écriture avec encodage UTF-8
        json.dump(summary, f, indent=2, ensure_ascii=False)  # Écrit le résumé au format JSON (indenté, avec caractères Unicode)
    
    print("=" * 60)  # Affiche une ligne de séparation
    print("Toutes les expériences sont terminées!")  # Affiche le message de fin
    print(f"Résultats sauvegardés dans : {results_dir}")  # Affiche le chemin des résultats
    print(f"Résumé comparatif : {summary_path}")  # Affiche le chemin du résumé
    print("=" * 60)  # Affiche une ligne de séparation


if __name__ == "__main__":  # Vérifie si le script est exécuté directement (pas importé)
    parser = argparse.ArgumentParser(  # Crée un parser d'arguments en ligne de commande
        description="Compare different parallel models for image grayscale conversion with synchronization."  # Description du programme
    )
    parser.add_argument("--images", default="./images", help="Folder with images")  # Argument pour le dossier d'images (défaut: ./images)
    parser.add_argument("--output", default="./output", help="Folder for output images")  # Argument pour le dossier de sortie (défaut: ./output)
    parser.add_argument("--results", default="./results", help="Folder for results")  # Argument pour le dossier de résultats (défaut: ./results)
    parser.add_argument("--threads", nargs="+", type=int, default=[2, 4, 8], help="Thread counts to test")  # Argument pour les nombres de threads (défaut: 2, 4, 8)
    parser.add_argument("--processes", nargs="+", type=int, default=[2, 4], help="Process counts to test")  # Argument pour les nombres de processus (défaut: 2, 4)
    args = parser.parse_args()  # Parse les arguments de la ligne de commande
    sizes = {"threads": args.threads, "processes": args.processes}  # Crée le dictionnaire avec les tailles à tester
    run_all(args.images, args.output, args.results, sizes)  # Lance toutes les expériences avec les paramètres fournis
