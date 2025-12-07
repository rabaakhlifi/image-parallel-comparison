# src/versions/multiprocessing_version.py
"""
Version avec multiprocessing démontrant :
1. Partage de données entre processus avec multiprocessing.Manager()
2. Synchronisation avec Lock multiprocessing
3. Comparaison avec threading (pas de GIL)

Ce module implémente le traitement parallèle des images avec des processus séparés.
Contrairement aux threads, les processus ont leur propre mémoire, ce qui permet
une vraie parallélisation sans limitation par le GIL.

Rôle détaillé :
- Crée un pool de processus pour traiter les images en parallèle
- Utilise multiprocessing.Pool pour distribuer le travail
- Démontre la synchronisation entre processus avec multiprocessing.Lock()
- Mesure les performances et métriques de synchronisation
- Compare avec threading (pas de GIL, mais synchronisation nécessaire pour ressources partagées)
"""
from multiprocessing import Pool, Manager  # Import de Pool pour créer un pool de processus et Manager pour partager des objets
from typing import List, Dict  # Types pour les annotations de type
from ..processor import convert_to_grayscale, set_global_logger  # Import de la fonction de conversion et du setter de logger
from ..common import Timer  # Import de la classe Timer pour mesurer le temps
import os  # Module pour les opérations sur le système de fichiers
from ..synchronization_tools import ProcessSafeFileLogger, ProcessSafeCounter  # Import des outils de synchronisation pour processus


# Fonction wrapper pour convertir une image (utilisée par multiprocessing.Pool)
def _convert_wrapper(args):
    """
    Wrapper pour la conversion d'image dans un processus séparé.
    Les processus ne partagent pas la mémoire, donc le logger doit être
    passé ou recréé dans chaque processus.
    
    Cette fonction est exécutée dans chaque processus worker. Elle reçoit
    les arguments sous forme de tuple et appelle convert_to_grayscale.
    """
    path, output_dir, thread_id, use_lock = args  # Décompose le tuple d'arguments en variables séparées
    return convert_to_grayscale(path, output_dir, thread_id=thread_id, use_lock=use_lock)  # Appelle la fonction de conversion et retourne le résultat


# Traite les images en parallèle en utilisant multiprocessing.Pool (processus séparés)
def process_multiprocessing(
    image_paths: List[str],  # Liste des chemins vers les images à traiter
    output_dir: str,  # Dossier où sauvegarder les images converties
    n_workers: int = None,  # Nombre de processus workers (None = nombre de CPU)
    use_lock: bool = True  # Si True, utilise un Lock multiprocessing pour protéger les zones critiques
) -> Dict:  # Retourne un dictionnaire avec les statistiques et métriques
    """
    Traite les images en parallèle avec des processus séparés.
    
    Différences avec threading :
    - Chaque processus a sa propre mémoire (pas de GIL)
    - Les verrous doivent être partagés via multiprocessing.Manager()
    - Pas de race condition sur les variables globales (mémoire séparée)
    - Mais nécessite synchronisation pour les ressources partagées (fichiers, etc.)
    
    Args:
        image_paths: Liste des chemins vers les images
        output_dir: Dossier de sortie
        n_workers: Nombre de processus workers
        use_lock: Si True, utilise un Lock multiprocessing pour protéger les zones critiques
    
    Returns:
        Dictionnaire avec les statistiques et métriques de synchronisation
    """
    import multiprocessing  # Import de multiprocessing (redondant mais gardé pour clarté)
    
    if n_workers is None:  # Si le nombre de workers n'est pas spécifié
        n_workers = os.cpu_count() or 2  # Utilise le nombre de CPU disponibles (ou 2 par défaut)
    
    # Créer le logger process-safe
    log_file = os.path.join(output_dir, "processing.log")  # Construit le chemin du fichier de log
    
    if use_lock:  # Si on doit utiliser un lock
        # Le logger doit être créé dans chaque processus
        # On passe le chemin du fichier et recréons le logger dans chaque worker
        logger = ProcessSafeFileLogger(log_file)  # Crée un logger process-safe avec lock multiprocessing
    else:  # Si on ne veut pas de protection
        logger = type('Logger', (), {'log_file': log_file})()  # Crée un objet logger minimal sans protection
    
    set_global_logger(logger)  # Définit le logger global (mais sera recréé dans chaque processus)
    
    t = Timer()  # Crée un chronomètre pour mesurer le temps total
    t.start()  # Démarre le chronomètre
    
    # Préparer les arguments pour chaque image
    args = [  # Crée une liste de tuples d'arguments pour chaque image
        (p, output_dir, f"P{i % n_workers}", use_lock)  # Tuple avec (chemin, dossier_sortie, id_processus, use_lock)
        for i, p in enumerate(image_paths)  # Parcourt toutes les images avec leur index
    ]
    
    with Pool(processes=n_workers) as pool:  # Crée un pool de n_workers processus (gestion automatique)
        results = pool.map(_convert_wrapper, args)  # Distribue les tâches aux processus et collecte les résultats
    
    total = t.stop()  # Arrête le chronomètre et récupère le temps total
    
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
        "n_workers": n_workers,  # Nombre de processus workers utilisés
        "use_lock": use_lock,  # Indique si un lock a été utilisé
        "sync_metrics": sync_metrics,  # Métriques de synchronisation
        "logger_metrics": logger_metrics  # Métriques du logger
    }