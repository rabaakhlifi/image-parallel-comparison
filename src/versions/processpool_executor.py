# src/versions/processpool_executor.py
"""
Version avec ProcessPoolExecutor démontrant :
1. API concurrent.futures avec processus
2. Synchronisation avec Lock multiprocessing
3. Partage de données via multiprocessing.Manager()

Ce module implémente le traitement parallèle des images avec ProcessPoolExecutor,
une API moderne de Python pour gérer les processus. Elle simplifie la gestion du
cycle de vie des processus et le retour des résultats via des futures.

Rôle détaillé :
- Utilise ProcessPoolExecutor pour créer et gérer un pool de processus
- Soumet les tâches de conversion via submit() qui retourne des futures
- Collecte les résultats au fur et à mesure avec as_completed()
- Démontre la synchronisation entre processus avec multiprocessing.Lock()
- Mesure les performances et métriques de synchronisation
- Compare avec ThreadPoolExecutor (pas de GIL, vraie parallélisation)
"""
from concurrent.futures import ProcessPoolExecutor, as_completed  # Import de ProcessPoolExecutor et as_completed pour gérer les futures
from typing import List, Dict  # Types pour les annotations de type
from ..processor import convert_to_grayscale, set_global_logger  # Import de la fonction de conversion et du setter de logger
from ..common import Timer  # Import de la classe Timer pour mesurer le temps
import os  # Module pour les opérations sur le système de fichiers
from ..synchronization_tools import ProcessSafeFileLogger  # Import de l'outil de synchronisation pour processus


# Fonction wrapper pour convertir une image (utilisée par ProcessPoolExecutor)
def _wrapper(args):
    """
    Wrapper pour la conversion d'image dans un processus séparé.
    Le logger doit être recréé dans chaque processus car la mémoire n'est pas partagée.
    
    Cette fonction est exécutée dans chaque processus worker. Elle reçoit
    les arguments sous forme de tuple, recrée le logger dans le processus,
    et appelle convert_to_grayscale.
    """
    path, output_dir, thread_id, use_lock, log_file = args  # Décompose le tuple d'arguments en variables séparées
    
    # Recréer le logger dans chaque processus
    if use_lock and log_file:  # Si on doit utiliser un lock et qu'un fichier de log est fourni
        from ..synchronization_tools import ProcessSafeFileLogger  # Import du logger process-safe (dans chaque processus)
        logger = ProcessSafeFileLogger(log_file)  # Crée un nouveau logger dans ce processus
        set_global_logger(logger)  # Définit le logger global pour ce processus
    
    return convert_to_grayscale(path, output_dir, thread_id=thread_id, use_lock=use_lock)  # Appelle la fonction de conversion et retourne le résultat


# Traite les images en parallèle en utilisant ProcessPoolExecutor (processus séparés)
def process_processpool(
    image_paths: List[str],  # Liste des chemins vers les images à traiter
    output_dir: str,  # Dossier où sauvegarder les images converties
    max_workers: int = None,  # Nombre maximum de processus (None = nombre de CPU)
    use_lock: bool = True  # Si True, utilise un Lock multiprocessing pour protéger les zones critiques
) -> Dict:  # Retourne un dictionnaire avec les statistiques et métriques
    """
    Traite les images en parallèle avec ProcessPoolExecutor.
    
    Différences avec ThreadPoolExecutor :
    - Chaque processus a sa propre mémoire (pas de GIL)
    - Les verrous doivent être partagés via multiprocessing
    - Nécessite synchronisation pour les ressources partagées (fichiers)
    
    Avantages :
    - Pas de limitation du GIL pour les tâches CPU-bound
    - Vraie parallélisation sur plusieurs cœurs
    
    Args:
        image_paths: Liste des chemins vers les images
        output_dir: Dossier de sortie
        max_workers: Nombre maximum de processus
        use_lock: Si True, utilise un Lock multiprocessing pour protéger les zones critiques
    
    Returns:
        Dictionnaire avec les statistiques et métriques de synchronisation
    """
    if max_workers is None:  # Si le nombre de workers n'est pas spécifié
        max_workers = os.cpu_count() or 2  # Utilise le nombre de CPU disponibles (ou 2 par défaut)
    
    # Créer le logger process-safe
    log_file = os.path.join(output_dir, "processing.log")  # Construit le chemin du fichier de log
    
    if use_lock:  # Si on doit utiliser un lock
        logger = ProcessSafeFileLogger(log_file)  # Crée un logger process-safe avec lock multiprocessing
    else:  # Si on ne veut pas de protection
        logger = type('Logger', (), {'log_file': log_file})()  # Crée un objet logger minimal sans protection
    
    set_global_logger(logger)  # Définit le logger global (mais sera recréé dans chaque processus)
    
    timer = Timer()  # Crée un chronomètre pour mesurer le temps total
    timer.start()  # Démarre le chronomètre
    results = []  # Liste pour stocker les résultats
    
    with ProcessPoolExecutor(max_workers=max_workers) as ex:  # Crée un pool de processus (gestion automatique)
        # Préparer les arguments avec le chemin du log pour chaque processus
        futures = {  # Crée un dictionnaire {future: chemin_image} pour suivre les tâches
            ex.submit(  # Soumet une tâche au pool et retourne un future
                _wrapper,  # Fonction wrapper à exécuter dans le processus
                (p, output_dir, f"P{i % max_workers}", use_lock, log_file)  # Tuple d'arguments (chemin, dossier_sortie, id_processus, use_lock, log_file)
            ): p  # Clé du dictionnaire : chemin de l'image
            for i, p in enumerate(image_paths)  # Parcourt toutes les images avec leur index
        }
        
        # Collecter les résultats au fur et à mesure
        for fut in as_completed(futures):  # Parcourt les futures au fur et à mesure de leur complétion
            res = fut.result()  # Récupère le résultat du future (bloque si pas encore prêt)
            results.append(res)  # Ajoute le résultat à la liste
    
    total = timer.stop()  # Arrête le chronomètre et récupère le temps total
    
    # Récupérer les métriques de synchronisation
    # Note: Les métriques du logger ne peuvent pas être récupérées directement
    # car elles sont dans des processus séparés. On peut les lire depuis le fichier.
    logger_metrics = {}  # Initialise le dictionnaire de métriques du logger
    if hasattr(logger, 'get_metrics'):  # Vérifie si le logger a une méthode get_metrics
        try:  # Bloc try pour gérer les erreurs possibles
            logger_metrics = logger.get_metrics()  # Essaie de récupérer les métriques (peut échouer car dans processus séparé)
        except:  # Capture toutes les exceptions
            pass  # Ignore les erreurs (les métriques peuvent ne pas être disponibles)
    
    sync_metrics = {}  # Initialise le dictionnaire de métriques de synchronisation
    if logger_metrics:  # Si le logger a fourni des métriques
        sync_metrics.update(logger_metrics)  # Fusionne les métriques du logger
    
    return {  # Retourne un dictionnaire avec toutes les statistiques
        "total_time": total,  # Temps total de traitement
        "n_images": len(image_paths),  # Nombre d'images traitées
        "runs": results,  # Liste de tous les résultats individuels
        "max_workers": max_workers,  # Nombre maximum de processus utilisés
        "use_lock": use_lock,  # Indique si un lock a été utilisé
        "sync_metrics": sync_metrics,  # Métriques de synchronisation
        "logger_metrics": logger_metrics  # Métriques du logger
    }
