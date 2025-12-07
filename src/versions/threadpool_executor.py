# src/versions/threadpool_executor.py
"""
Version avec ThreadPoolExecutor démontrant :
1. API concurrent.futures avec threads
2. Synchronisation avec Lock
3. Comparaison avec threading manuel

Ce module implémente le traitement parallèle des images avec ThreadPoolExecutor,
une API moderne de Python pour gérer les threads. Elle simplifie la gestion du
cycle de vie des threads et le retour des résultats via des futures.

Rôle détaillé :
- Utilise ThreadPoolExecutor pour créer et gérer un pool de threads
- Soumet les tâches de conversion via submit() qui retourne des futures
- Collecte les résultats au fur et à mesure avec as_completed()
- Démontre la synchronisation avec Lock et Semaphore
- Mesure les performances et métriques de synchronisation
"""
from concurrent.futures import ThreadPoolExecutor, as_completed  # Import de ThreadPoolExecutor et as_completed pour gérer les futures
from typing import List, Dict  # Types pour les annotations de type
from ..processor import convert_to_grayscale, set_global_logger  # Import de la fonction de conversion et du setter de logger
from ..common import Timer  # Import de la classe Timer pour mesurer le temps
import os  # Module pour les opérations sur le système de fichiers
from ..synchronization_tools import ThreadSafeFileLogger, SemaphoreFileLogger  # Import des outils de synchronisation pour threads


# Traite les images en parallèle en utilisant ThreadPoolExecutor (threads)
def process_threadpool(
    image_paths: List[str],  # Liste des chemins vers les images à traiter
    output_dir: str,  # Dossier où sauvegarder les images converties
    max_workers: int = None,  # Nombre maximum de threads (None = valeur par défaut)
    use_lock: bool = True,  # Si True, utilise un Lock pour protéger les zones critiques
    use_semaphore: bool = False,  # Si True, utilise un Semaphore pour limiter l'accès au log
    max_concurrent_log: int = 2  # Nombre maximum de threads pouvant écrire simultanément dans le log
) -> Dict:  # Retourne un dictionnaire avec les statistiques et métriques
    """
    Traite les images en parallèle avec ThreadPoolExecutor.
    
    Avantages par rapport à threading manuel :
    - API plus simple et moderne
    - Gestion automatique du cycle de vie des threads
    - Retour de résultats via futures
    
    Démontre :
    - Synchronisation avec Lock via le logger thread-safe
    - Limitation d'accès avec Semaphore
    
    Args:
        image_paths: Liste des chemins vers les images
        output_dir: Dossier de sortie
        max_workers: Nombre maximum de threads
        use_lock: Si True, utilise un Lock pour protéger les zones critiques
        use_semaphore: Si True, utilise un Semaphore pour limiter l'accès au log
        max_concurrent_log: Nombre maximum de threads pouvant écrire simultanément
    
    Returns:
        Dictionnaire avec les statistiques et métriques de synchronisation
    """
    # Créer le logger selon le type de synchronisation
    log_file = os.path.join(output_dir, "processing.log")  # Construit le chemin du fichier de log
    
    if use_semaphore:  # Si on doit utiliser un sémaphore
        logger = SemaphoreFileLogger(log_file, max_concurrent_log)  # Crée un logger avec sémaphore (limite l'accès concurrent)
    elif use_lock:  # Si on doit utiliser un lock
        logger = ThreadSafeFileLogger(log_file)  # Crée un logger thread-safe avec lock
    else:  # Si on ne veut pas de protection
        logger = type('Logger', (), {'log_file': log_file})()  # Crée un objet logger minimal sans protection
    
    set_global_logger(logger)  # Définit le logger global pour toutes les conversions
    
    timer = Timer()  # Crée un chronomètre pour mesurer le temps total
    timer.start()  # Démarre le chronomètre
    results = []  # Liste pour stocker les résultats
    
    with ThreadPoolExecutor(max_workers=max_workers) as ex:  # Crée un pool de threads (gestion automatique)
        # Soumettre toutes les tâches
        futures = {  # Crée un dictionnaire {future: chemin_image} pour suivre les tâches
            ex.submit(  # Soumet une tâche au pool et retourne un future
                convert_to_grayscale,  # Fonction à exécuter
                p,  # Chemin de l'image
                output_dir,  # Dossier de sortie
                thread_id=f"T{i % (max_workers or 4)}",  # Génère un identifiant de thread
                use_lock=use_lock  # Indique si on doit utiliser le lock
            ): p  # Clé du dictionnaire : chemin de l'image
            for i, p in enumerate(image_paths)  # Parcourt toutes les images avec leur index
        }
        
        # Collecter les résultats au fur et à mesure
        for fut in as_completed(futures):  # Parcourt les futures au fur et à mesure de leur complétion
            res = fut.result()  # Récupère le résultat du future (bloque si pas encore prêt)
            results.append(res)  # Ajoute le résultat à la liste
    
    total = timer.stop()  # Arrête le chronomètre et récupère le temps total
    
    # Récupérer les métriques de synchronisation
    logger_metrics = {}  # Initialise le dictionnaire de métriques du logger
    if hasattr(logger, 'get_metrics'):  # Vérifie si le logger a une méthode get_metrics
        logger_metrics = logger.get_metrics()  # Récupère les métriques de synchronisation du logger
    
    sync_metrics = {}  # Initialise le dictionnaire de métriques de synchronisation
    if logger_metrics:  # Si le logger a fourni des métriques
        sync_metrics.update(logger_metrics)  # Fusionne les métriques du logger
    
    return {  # Retourne un dictionnaire avec toutes les statistiques
        "total_time": total,  # Temps total de traitement
        "n_images": len(image_paths),  # Nombre d'images traitées
        "runs": results,  # Liste de tous les résultats individuels
        "max_workers": max_workers,  # Nombre maximum de threads utilisés
        "use_lock": use_lock,  # Indique si un lock a été utilisé
        "use_semaphore": use_semaphore,  # Indique si un sémaphore a été utilisé
        "sync_metrics": sync_metrics,  # Métriques de synchronisation
        "logger_metrics": logger_metrics  # Métriques du logger
    }
