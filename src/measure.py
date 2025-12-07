# src/measure.py
"""
Module de mesure des performances incluant les métriques de synchronisation.

Ce module mesure les performances d'exécution des différentes approches de parallélisme
et collecte les métriques de synchronisation (temps d'attente sur verrous, contentions, etc.).

Rôle détaillé :
- Mesure le temps total d'exécution d'une fonction
- Calcule le temps moyen par image
- Calcule le débit (images par seconde)
- Collecte les métriques de synchronisation (temps d'attente, contentions)
- Exporte les résultats au format JSON et CSV
- Inclut optionnellement le monitoring CPU avec psutil
"""
import time  # Module pour mesurer le temps (perf_counter pour haute précision)
import psutil  # Module pour le monitoring système (CPU, mémoire) - optionnel
from typing import Callable, List, Dict, Any  # Types pour les annotations de type
from .common import save_results_json, save_results_csv, ensure_dirs, safe_filename  # Import des fonctions utilitaires
import os  # Module pour les opérations sur le système de fichiers
from statistics import mean  # Import de mean (non utilisé directement mais gardé pour compatibilité)


# Mesure les performances d'exécution d'une fonction (temps total, temps moyen, débit)
def measure_run(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Mesure le temps total, temps moyen par image, débit (img/s) et métriques de synchronisation.
    
    Cette fonction exécute une fonction de traitement et mesure toutes les métriques
    de performance et de synchronisation. Elle peut optionnellement collecter
    des échantillons d'utilisation CPU.
    
    Args:
        func: Fonction à mesurer (doit retourner un dict avec 'total_time', 'n_images', 'runs')
        *args: Arguments positionnels pour func
        **kwargs: Arguments nommés pour func
    
    Returns:
        Dictionnaire avec toutes les métriques de performance et de synchronisation
    """
    # CPU sampling (optionnel) si psutil installé
    cpu_samples = []  # Liste pour stocker les échantillons d'utilisation CPU
    sampling = kwargs.pop("cpu_sampling", False)  # Récupère l'option de sampling CPU (retire de kwargs)
    sample_interval = kwargs.pop("sample_interval", 0.05)  # Intervalle d'échantillonnage en secondes (retire de kwargs)
    
    if sampling and psutil:  # Si le sampling CPU est activé et que psutil est disponible
        _stop = False  # Variable de contrôle pour arrêter le thread de sampling
        def _sample():  # Fonction interne pour échantillonner le CPU dans un thread séparé
            while not _stop:  # Boucle jusqu'à ce que _stop soit True
                cpu_samples.append(psutil.cpu_percent(interval=None))  # Ajoute l'utilisation CPU actuelle à la liste
                time.sleep(sample_interval)  # Attend avant le prochain échantillon
        import threading  # Import de threading pour créer un thread de sampling
        samp_thread = threading.Thread(target=_sample, daemon=True)  # Crée un thread daemon pour le sampling
        samp_thread.start()  # Démarre le thread de sampling
    
    t0 = time.perf_counter()  # Enregistre le temps de début (haute précision)
    res = func(*args, **kwargs)  # Exécute la fonction à mesurer avec ses arguments
    total = time.perf_counter() - t0  # Calcule le temps total (temps actuel - temps de début)
    
    if sampling and psutil:  # Si le sampling CPU était activé
        _stop = True  # Indique au thread de sampling de s'arrêter
        time.sleep(sample_interval * 1.1)  # Attend un peu plus que l'intervalle pour laisser le thread se terminer
    
    n = res.get("n_images", len(res.get("runs", [])))  # Récupère le nombre d'images (depuis n_images ou calcule depuis runs)
    avg = total / n if n else None  # Calcule le temps moyen par image (temps total / nombre d'images)
    throughput = n / total if total and n else None  # Calcule le débit (nombre d'images / temps total)
    
    # Extraire les métriques de synchronisation si disponibles
    sync_metrics = res.get("sync_metrics", {})  # Récupère les métriques de synchronisation depuis le résultat
    logger_metrics = res.get("logger_metrics", {})  # Récupère les métriques du logger depuis le résultat
    
    # Combiner toutes les métriques de synchronisation
    all_sync_metrics = {}  # Initialise le dictionnaire combiné
    if sync_metrics:  # Si des métriques de synchronisation existent
        all_sync_metrics.update(sync_metrics)  # Ajoute les métriques de synchronisation
    if logger_metrics:  # Si des métriques du logger existent
        all_sync_metrics.update(logger_metrics)  # Ajoute les métriques du logger (écrase les doublons)
    
    result = {  # Crée le dictionnaire de résultat final
        "total_time": total,  # Temps total d'exécution en secondes
        "n_images": n,  # Nombre d'images traitées
        "avg_time_per_image": avg,  # Temps moyen par image en secondes
        "throughput_img_per_sec": throughput,  # Débit en images par seconde
        "cpu_samples": cpu_samples,  # Liste des échantillons d'utilisation CPU
        "raw_result": res,  # Résultat brut de la fonction (pour référence)
        "sync_metrics": all_sync_metrics  # Métriques de synchronisation combinées
    }
    
    return result  # Retourne le dictionnaire complet avec toutes les métriques


# Exporte les résultats de mesure au format JSON et CSV
def export_results(base_path: str, name: str, data: Dict):
    """
    Exporte les résultats de mesure au format JSON et CSV.
    Inclut les métriques de synchronisation dans les fichiers CSV.
    
    Cette fonction sauvegarde les résultats de mesure dans deux formats :
    - JSON : format complet avec toutes les données
    - CSV : format tabulaire avec les métriques principales et de synchronisation
    
    Args:
        base_path: Chemin de base pour sauvegarder les fichiers
        name: Nom de base pour les fichiers (sans extension)
        data: Dictionnaire contenant toutes les métriques à exporter
    """
    os.makedirs(base_path, exist_ok=True)  # Crée le dossier de base s'il n'existe pas
    
    # Sauvegarde JSON complète
    save_results_json(os.path.join(base_path, f"{name}.json"), data)  # Sauvegarde toutes les données au format JSON
    
    # Sauvegarde CSV avec métriques principales
    headers = ["metric", "value"]  # En-têtes du fichier CSV (métrique, valeur)
    rows = [  # Liste des lignes de données
        ["total_time", data["total_time"]],  # Temps total d'exécution
        ["n_images", data["n_images"]],  # Nombre d'images traitées
        ["avg_time_per_image", data["avg_time_per_image"]],  # Temps moyen par image
        ["throughput_img_per_sec", data["throughput_img_per_sec"]],  # Débit en images/seconde
        ["cpu_sample_mean", (sum(data["cpu_samples"])/len(data["cpu_samples"])) if data["cpu_samples"] else None]  # Utilisation CPU moyenne (si échantillons disponibles)
    ]
    
    # Ajouter les métriques de synchronisation si disponibles
    sync_metrics = data.get("sync_metrics", {})  # Récupère les métriques de synchronisation
    if sync_metrics:  # Si des métriques de synchronisation existent
        rows.append(["sync_total_lock_wait_time", sync_metrics.get("total_lock_wait_time", 0)])  # Temps total d'attente sur verrous
        rows.append(["sync_avg_lock_wait_time", sync_metrics.get("avg_lock_wait_time", 0)])  # Temps moyen d'attente sur verrous
        rows.append(["sync_max_lock_wait_time", sync_metrics.get("max_lock_wait_time", 0)])  # Temps maximum d'attente sur verrous
        rows.append(["sync_total_semaphore_wait_time", sync_metrics.get("total_semaphore_wait_time", 0)])  # Temps total d'attente sur sémaphores
        rows.append(["sync_avg_semaphore_wait_time", sync_metrics.get("avg_semaphore_wait_time", 0)])  # Temps moyen d'attente sur sémaphores
        rows.append(["sync_lock_acquire_count", sync_metrics.get("lock_acquire_count", 0)])  # Nombre d'acquisitions de verrous
        rows.append(["sync_semaphore_acquire_count", sync_metrics.get("semaphore_acquire_count", 0)])  # Nombre d'acquisitions de sémaphores
        rows.append(["sync_contention_count", sync_metrics.get("contention_count", 0)])  # Nombre de contentions
        rows.append(["sync_total_wait_time", sync_metrics.get("total_wait_time", 0)])  # Temps total d'attente (verrous + sémaphores)
    
    save_results_csv(os.path.join(base_path, f"{name}_summary.csv"), headers, rows)  # Sauvegarde les métriques au format CSV
