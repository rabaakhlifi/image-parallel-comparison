# src/versions/threading_version.py
"""
Version avec threading démontrant :
1. Race condition (sans lock)
2. Correction avec Lock (mutex)
3. Utilisation de Semaphore pour limiter l'accès concurrent

Ce module implémente le traitement parallèle des images avec des threads Python.
Il démontre explicitement les problèmes de race conditions et leur correction
avec des mécanismes de synchronisation.

Rôle détaillé :
- Crée plusieurs threads pour traiter les images en parallèle
- Utilise une Queue pour distribuer le travail entre les threads
- Démontre les race conditions avec une version sans protection
- Corrige les race conditions avec des Lock (mutex)
- Limite l'accès concurrent avec des Sémaphores
- Mesure les temps d'attente sur les verrous
- Collecte les métriques de synchronisation
"""
import threading  # Module pour la création et gestion de threads
from typing import List, Dict  # Types pour les annotations de type
from ..processor import convert_to_grayscale, set_global_logger  # Import de la fonction de conversion et du setter de logger
from ..common import Timer  # Import de la classe Timer pour mesurer le temps
from queue import Queue, Empty  # Import de Queue pour distribuer le travail et Empty pour les exceptions
from ..synchronization_tools import (  # Import des outils de synchronisation
    ThreadSafeFileLogger,  # Logger thread-safe avec Lock
    SemaphoreFileLogger,  # Logger avec Sémaphore pour limiter l'accès
    UnsafeCounter,  # Compteur non thread-safe (démonstration)
    ThreadSafeCounter  # Compteur thread-safe avec Lock
)
import os  # Module pour les opérations sur le système de fichiers
import time  # Module pour mesurer le temps (perf_counter pour haute précision)


# Fonction exécutée par chaque thread : récupère une image de la queue et la traite
def worker_without_lock(in_q: Queue, out_list: List, output_dir: str, lock: threading.Lock, thread_id: str):
    """
    Worker sans protection pour démontrer les race conditions.
    L'écriture dans la liste partagée n'est pas protégée.
    
    Cette fonction est exécutée par chaque thread et traite les images
    une par une. Elle ne protège pas l'accès à la liste partagée, ce qui
    peut causer des race conditions.
    """
    while True:  # Boucle infinie jusqu'à ce que la queue soit vide
        try:  # Bloc try pour gérer l'exception Empty
            path = in_q.get_nowait()  # Récupère une image de la queue sans attendre (lève Empty si la queue est vide)
        except Empty:  # Si la queue est vide, on a terminé
            return  # Sort de la fonction (le thread se termine)
        
        t = Timer()  # Crée un chronomètre pour mesurer le temps de traitement de cette image
        t.start()  # Démarre le chronomètre
        # Conversion sans lock (peut causer des race conditions dans le log)
        res = convert_to_grayscale(path, output_dir, thread_id=thread_id, use_lock=False)  # Convertit l'image SANS protection (race condition possible)
        elapsed = t.stop()  # Arrête le chronomètre et récupère le temps écoulé
        
        # ZONE CRITIQUE NON PROTÉGÉE : Ajout dans la liste partagée
        # Sans lock, plusieurs threads peuvent modifier simultanément
        out_list.append({  # Ajoute le résultat à la liste partagée (NON PROTÉGÉ - race condition possible)
            "image": path,  # Chemin de l'image traitée
            "elapsed": elapsed,  # Temps écoulé pour traiter cette image
            "success": res.get("success", False),  # Indique si la conversion a réussi
            "thread_id": thread_id  # Identifiant du thread
        })
        in_q.task_done()  # Indique à la queue qu'une tâche est terminée


# Fonction exécutée par chaque thread : récupère une image de la queue et la traite
def worker_with_lock(in_q: Queue, out_list: List, output_dir: str, lock: threading.Lock, thread_id: str):
    """
    Worker avec protection Lock pour éviter les race conditions.
    L'écriture dans la liste partagée est protégée par un mutex.
    
    Cette fonction est exécutée par chaque thread et traite les images
    une par une. Elle protège l'accès à la liste partagée avec un verrou,
    garantissant qu'un seul thread peut modifier la liste à la fois.
    """
    while True:  # Boucle infinie jusqu'à ce que la queue soit vide
        try:  # Bloc try pour gérer l'exception Empty
            path = in_q.get_nowait()  # Récupère une image de la queue sans attendre (lève Empty si la queue est vide)
        except Empty:  # Si la queue est vide, on a terminé
            return  # Sort de la fonction (le thread se termine)
        
        t = Timer()  # Crée un chronomètre pour mesurer le temps de traitement de cette image
        t.start()  # Démarre le chronomètre
        # Conversion avec lock (thread-safe)
        res = convert_to_grayscale(path, output_dir, thread_id=thread_id, use_lock=True)  # Convertit l'image AVEC protection (thread-safe)
        elapsed = t.stop()  # Arrête le chronomètre et récupère le temps écoulé
        
        # ZONE CRITIQUE PROTÉGÉE : Ajout dans la liste partagée avec Lock
        start_wait = time.perf_counter()  # Enregistre le temps avant d'essayer d'acquérir le verrou
        with lock:  # Acquiert le verrou (bloque si un autre thread l'a déjà)
            wait_time = time.perf_counter() - start_wait  # Calcule le temps d'attente pour acquérir le verrou
            out_list.append({  # Ajoute le résultat à la liste partagée (PROTÉGÉ par le verrou)
                "image": path,  # Chemin de l'image traitée
                "elapsed": elapsed,  # Temps écoulé pour traiter cette image
                "success": res.get("success", False),  # Indique si la conversion a réussi
                "thread_id": thread_id,  # Identifiant du thread
                "lock_wait_time": wait_time  # Temps passé en attente du verrou
            })
            # Le verrou est automatiquement libéré à la sortie du bloc with
        in_q.task_done()  # Indique à la queue qu'une tâche est terminée


# Traite les images en parallèle en utilisant des threads Python
def process_threading(
    image_paths: List[str],  # Liste des chemins vers les images à traiter
    output_dir: str,  # Dossier où sauvegarder les images converties
    n_threads: int = 4,  # Nombre de threads à créer (par défaut: 4)
    use_lock: bool = True,  # Si True, utilise un Lock pour protéger les zones critiques
    use_semaphore: bool = False,  # Si True, utilise un Semaphore pour limiter l'accès au log
    max_concurrent_log: int = 2  # Nombre maximum de threads pouvant écrire simultanément dans le log
) -> Dict:  # Retourne un dictionnaire avec les statistiques et métriques
    """
    Traite les images en parallèle avec des threads.
    
    Démontre :
    - Race condition si use_lock=False
    - Correction avec Lock (mutex) si use_lock=True
    - Limitation d'accès avec Semaphore si use_semaphore=True
    
    Args:
        image_paths: Liste des chemins vers les images
        output_dir: Dossier de sortie
        n_threads: Nombre de threads
        use_lock: Si True, utilise un Lock pour protéger les zones critiques
        use_semaphore: Si True, utilise un Semaphore pour limiter l'accès au log
        max_concurrent_log: Nombre maximum de threads pouvant écrire simultanément dans le log
    
    Returns:
        Dictionnaire avec les statistiques et métriques de synchronisation
    """
    from queue import Queue  # Import de Queue (redondant mais gardé pour clarté)
    
    # Créer le logger selon le type de synchronisation
    log_file = os.path.join(output_dir, "processing.log")  # Construit le chemin du fichier de log
    
    if use_semaphore:  # Si on doit utiliser un sémaphore
        logger = SemaphoreFileLogger(log_file, max_concurrent_log)  # Crée un logger avec sémaphore (limite l'accès concurrent)
    elif use_lock:  # Si on doit utiliser un lock
        logger = ThreadSafeFileLogger(log_file)  # Crée un logger thread-safe avec lock
    else:  # Si on ne veut pas de protection
        # Logger sans protection (pour démontrer les race conditions)
        logger = type('Logger', (), {'log_file': log_file})()  # Crée un objet logger minimal sans protection
    
    set_global_logger(logger)  # Définit le logger global pour toutes les conversions
    
    q = Queue()  # Crée une queue pour distribuer le travail entre les threads
    for p in image_paths:  # Parcourt toutes les images
        q.put(p)  # Ajoute chaque image à la queue
    
    results = []  # Liste partagée pour stocker les résultats (zone critique)
    lock = threading.Lock()  # Crée un verrou pour protéger l'accès à la liste results
    threads = []  # Liste pour stocker les objets threads
    main_timer = Timer()  # Crée un chronomètre pour mesurer le temps total
    main_timer.start()  # Démarre le chronomètre
    
    # Choisir le worker selon le type de synchronisation
    worker_func = worker_with_lock if use_lock else worker_without_lock  # Sélectionne la fonction worker appropriée
    
    for i in range(n_threads):  # Crée n_threads threads
        thread_id = f"T{i}"  # Génère un identifiant unique pour ce thread
        t = threading.Thread(  # Crée un nouveau thread
            target=worker_func,  # Fonction à exécuter dans le thread
            args=(q, results, output_dir, lock, thread_id),  # Arguments à passer à la fonction
            daemon=True  # Thread daemon (se termine si le programme principal se termine)
        )
        t.start()  # Démarre le thread
        threads.append(t)  # Ajoute le thread à la liste
    
    q.join()  # Attend que toutes les tâches de la queue soient terminées (bloque jusqu'à ce que toutes les images soient traitées)
    total = main_timer.stop()  # Arrête le chronomètre et récupère le temps total
    
    # Récupérer les métriques de synchronisation du logger
    logger_metrics = {}  # Initialise le dictionnaire de métriques du logger
    if hasattr(logger, 'get_metrics'):  # Vérifie si le logger a une méthode get_metrics
        logger_metrics = logger.get_metrics()  # Récupère les métriques de synchronisation du logger
    
    # Calculer les métriques de lock depuis les résultats
    lock_wait_times = [r.get("lock_wait_time", 0) for r in results if "lock_wait_time" in r]  # Extrait tous les temps d'attente sur verrous depuis les résultats
    total_lock_wait = sum(lock_wait_times)  # Calcule la somme de tous les temps d'attente
    
    sync_metrics = {  # Crée un dictionnaire avec les métriques de synchronisation
        "total_lock_wait_time": total_lock_wait,  # Temps total passé en attente sur les verrous
        "avg_lock_wait_time": total_lock_wait / len(lock_wait_times) if lock_wait_times else 0,  # Temps moyen d'attente sur les verrous
        "max_lock_wait_time": max(lock_wait_times) if lock_wait_times else 0,  # Temps maximum d'attente sur un verrou
        "lock_wait_count": len([w for w in lock_wait_times if w > 0])  # Nombre de fois où un thread a dû attendre (temps > 0)
    }
    
    # Fusionner avec les métriques du logger
    if logger_metrics:  # Si le logger a fourni des métriques
        sync_metrics.update(logger_metrics)  # Fusionne les métriques du logger avec les métriques calculées
    
    return {  # Retourne un dictionnaire avec toutes les statistiques
        "total_time": total,  # Temps total de traitement
        "n_images": len(image_paths),  # Nombre d'images traitées
        "runs": results,  # Liste de tous les résultats individuels
        "n_threads": n_threads,  # Nombre de threads utilisés
        "use_lock": use_lock,  # Indique si un lock a été utilisé
        "use_semaphore": use_semaphore,  # Indique si un sémaphore a été utilisé
        "sync_metrics": sync_metrics,  # Métriques de synchronisation
        "logger_metrics": logger_metrics  # Métriques du logger
    }
