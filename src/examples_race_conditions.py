# src/examples_race_conditions.py
"""
Module démonstratif des race conditions et de leur correction avec des verrous.
Ce module peut être exécuté indépendamment pour comprendre les concepts.

Ce module contient des fonctions de démonstration pédagogiques qui illustrent
les concepts de synchronisation : race conditions, mutex, sémaphores, et zones critiques.

Rôle détaillé :
- Démontre les race conditions avec un compteur non thread-safe
- Montre la correction avec un compteur thread-safe (Lock)
- Illustre l'écriture dans un fichier comme zone critique
- Démontre l'utilisation d'un sémaphore pour limiter l'accès concurrent
- Peut être exécuté directement pour voir les démonstrations en action
"""
import threading  # Module pour la création et gestion de threads
import time  # Module pour mesurer le temps et faire des pauses
from .synchronization_tools import UnsafeCounter, ThreadSafeCounter, ThreadSafeFileLogger, SemaphoreFileLogger  # Import des outils de synchronisation


def demonstrate_race_condition():
    """
    Démontre une race condition avec un compteur non thread-safe.
    Plusieurs threads incrémentent le même compteur sans synchronisation.
    
    Cette fonction montre ce qui se passe quand plusieurs threads accèdent
    simultanément à une ressource partagée sans protection. Le résultat
    final sera incorrect (inférieur à la valeur attendue).
    """
    print("=" * 60)  # Affiche une ligne de séparation (60 caractères '=')
    print("DÉMONSTRATION : Race Condition (sans verrou)")  # Affiche le titre de la démonstration
    print("=" * 60)  # Affiche une ligne de séparation
    
    unsafe_counter = UnsafeCounter(0)  # Crée un compteur non thread-safe avec valeur initiale 0
    num_threads = 10  # Nombre de threads à créer
    increments_per_thread = 100  # Nombre d'incréments que chaque thread effectuera
    
    def increment_unsafe():  # Fonction exécutée par chaque thread
        for _ in range(increments_per_thread):  # Boucle pour incrémenter le compteur plusieurs fois
            unsafe_counter.increment()  # Incrémente le compteur (SANS protection - race condition possible)
    
    threads = []  # Liste pour stocker les objets threads
    start_time = time.perf_counter()  # Enregistre le temps de début (haute précision)
    
    for _ in range(num_threads):  # Crée num_threads threads
        t = threading.Thread(target=increment_unsafe)  # Crée un thread qui exécutera increment_unsafe
        t.start()  # Démarre le thread
        threads.append(t)  # Ajoute le thread à la liste
    
    for t in threads:  # Parcourt tous les threads
        t.join()  # Attend que chaque thread se termine (bloque jusqu'à la fin)
    
    elapsed = time.perf_counter() - start_time  # Calcule le temps écoulé (temps actuel - temps de début)
    final_value = unsafe_counter.get()  # Récupère la valeur finale du compteur (probablement incorrecte)
    expected_value = num_threads * increments_per_thread  # Calcule la valeur attendue (10 * 100 = 1000)
    
    print(f"Nombre de threads : {num_threads}")  # Affiche le nombre de threads utilisés
    print(f"Incréments par thread : {increments_per_thread}")  # Affiche le nombre d'incréments par thread
    print(f"Valeur attendue : {expected_value}")  # Affiche la valeur attendue (1000)
    print(f"Valeur obtenue : {final_value}")  # Affiche la valeur obtenue (probablement < 1000)
    print(f"Erreur : {expected_value - final_value} (race condition détectée!)")  # Affiche l'erreur (différence)
    print(f"Temps écoulé : {elapsed:.4f}s")  # Affiche le temps écoulé avec 4 décimales
    print()  # Ligne vide pour la lisibilité


def demonstrate_thread_safe_counter():
    """
    Démontre la correction de la race condition avec un compteur thread-safe.
    
    Cette fonction montre comment un Lock (mutex) corrige le problème de
    race condition. Le résultat final sera correct (égal à la valeur attendue),
    mais le temps d'exécution sera légèrement plus long à cause de la synchronisation.
    """
    print("=" * 60)  # Affiche une ligne de séparation
    print("DÉMONSTRATION : Compteur Thread-Safe (avec Lock)")  # Affiche le titre de la démonstration
    print("=" * 60)  # Affiche une ligne de séparation
    
    safe_counter = ThreadSafeCounter(0)  # Crée un compteur thread-safe avec valeur initiale 0
    num_threads = 10  # Nombre de threads à créer
    increments_per_thread = 100  # Nombre d'incréments que chaque thread effectuera
    
    def increment_safe():  # Fonction exécutée par chaque thread
        for _ in range(increments_per_thread):  # Boucle pour incrémenter le compteur plusieurs fois
            safe_counter.increment()  # Incrémente le compteur (AVEC protection - thread-safe)
    
    threads = []  # Liste pour stocker les objets threads
    start_time = time.perf_counter()  # Enregistre le temps de début
    
    for _ in range(num_threads):  # Crée num_threads threads
        t = threading.Thread(target=increment_safe)  # Crée un thread qui exécutera increment_safe
        t.start()  # Démarre le thread
        threads.append(t)  # Ajoute le thread à la liste
    
    for t in threads:  # Parcourt tous les threads
        t.join()  # Attend que chaque thread se termine
    
    elapsed = time.perf_counter() - start_time  # Calcule le temps écoulé
    final_value = safe_counter.get()  # Récupère la valeur finale du compteur (correcte)
    expected_value = num_threads * increments_per_thread  # Calcule la valeur attendue (1000)
    metrics = safe_counter.get_metrics()  # Récupère les métriques de synchronisation
    
    print(f"Nombre de threads : {num_threads}")  # Affiche le nombre de threads utilisés
    print(f"Incréments par thread : {increments_per_thread}")  # Affiche le nombre d'incréments par thread
    print(f"Valeur attendue : {expected_value}")  # Affiche la valeur attendue (1000)
    print(f"Valeur obtenue : {final_value}")  # Affiche la valeur obtenue (1000 - correcte!)
    print(f"Erreur : {expected_value - final_value} (aucune erreur!)")  # Affiche l'erreur (0)
    print(f"Temps écoulé : {elapsed:.4f}s")  # Affiche le temps écoulé
    print(f"Temps total passé en attente sur verrous : {metrics['total_lock_wait_time']:.4f}s")  # Affiche le temps d'attente sur verrous
    print(f"Nombre de contentions : {metrics['contention_count']}")  # Affiche le nombre de contentions
    print()  # Ligne vide pour la lisibilité


def demonstrate_critical_section_file():
    """
    Démontre l'écriture dans un fichier comme zone critique.
    Sans synchronisation, les écritures peuvent se mélanger.
    
    Cette fonction montre comment l'écriture dans un fichier constitue une
    zone critique qui nécessite une synchronisation. Avec un Lock, toutes
    les écritures sont correctement sérialisées.
    """
    print("=" * 60)  # Affiche une ligne de séparation
    print("DÉMONSTRATION : Zone Critique - Écriture Fichier (avec Lock)")  # Affiche le titre de la démonstration
    print("=" * 60)  # Affiche une ligne de séparation
    
    log_file = "demo_critical_section.log"  # Nom du fichier de log à créer
    logger = ThreadSafeFileLogger(log_file)  # Crée un logger thread-safe avec Lock
    num_threads = 5  # Nombre de threads à créer
    messages_per_thread = 20  # Nombre de messages que chaque thread écrira
    
    def write_messages(thread_id):  # Fonction exécutée par chaque thread
        for i in range(messages_per_thread):  # Boucle pour écrire plusieurs messages
            logger.log(f"Thread-{thread_id}: Message-{i}")  # Écrit un message dans le log (protégé par Lock)
    
    threads = []  # Liste pour stocker les objets threads
    start_time = time.perf_counter()  # Enregistre le temps de début
    
    for i in range(num_threads):  # Crée num_threads threads
        t = threading.Thread(target=write_messages, args=(i,))  # Crée un thread qui exécutera write_messages avec l'ID i
        t.start()  # Démarre le thread
        threads.append(t)  # Ajoute le thread à la liste
    
    for t in threads:  # Parcourt tous les threads
        t.join()  # Attend que chaque thread se termine
    
    elapsed = time.perf_counter() - start_time  # Calcule le temps écoulé
    metrics = logger.get_metrics()  # Récupère les métriques de synchronisation du logger
    
    # Vérifier le fichier
    with open(log_file, 'r') as f:  # Ouvre le fichier de log en mode lecture
        lines = f.readlines()  # Lit toutes les lignes du fichier
    
    print(f"Nombre de threads : {num_threads}")  # Affiche le nombre de threads utilisés
    print(f"Messages par thread : {messages_per_thread}")  # Affiche le nombre de messages par thread
    print(f"Total de lignes écrites : {len(lines)}")  # Affiche le nombre total de lignes écrites (devrait être 100)
    print(f"Temps écoulé : {elapsed:.4f}s")  # Affiche le temps écoulé
    print(f"Temps total passé en attente sur verrous : {metrics['total_lock_wait_time']:.4f}s")  # Affiche le temps d'attente sur verrous
    print(f"Nombre d'acquisitions de verrous : {metrics['lock_acquire_count']}")  # Affiche le nombre d'acquisitions de verrous
    print(f"Fichier créé : {log_file}")  # Affiche le nom du fichier créé
    print()  # Ligne vide pour la lisibilité


def demonstrate_semaphore():
    """
    Démontre l'utilisation d'un sémaphore pour limiter l'accès concurrent.
    
    Cette fonction montre comment un sémaphore permet de limiter le nombre
    de threads pouvant accéder simultanément à une ressource, tout en
    permettant plus d'un accès à la fois (contrairement au Lock).
    """
    print("=" * 60)  # Affiche une ligne de séparation
    print("DÉMONSTRATION : Sémaphore (limitation d'accès concurrent)")  # Affiche le titre de la démonstration
    print("=" * 60)  # Affiche une ligne de séparation
    
    log_file = "demo_semaphore.log"  # Nom du fichier de log à créer
    max_concurrent = 2  # Seulement 2 threads peuvent écrire simultanément
    logger = SemaphoreFileLogger(log_file, max_concurrent)  # Crée un logger avec sémaphore (2 accès max)
    num_threads = 5  # Nombre de threads à créer
    messages_per_thread = 10  # Nombre de messages que chaque thread écrira
    
    def write_messages(thread_id):  # Fonction exécutée par chaque thread
        for i in range(messages_per_thread):  # Boucle pour écrire plusieurs messages
            logger.log(f"Thread-{thread_id}: Message-{i}")  # Écrit un message dans le log (protégé par Sémaphore)
            time.sleep(0.01)  # Simule un traitement (pause de 10ms)
    
    threads = []  # Liste pour stocker les objets threads
    start_time = time.perf_counter()  # Enregistre le temps de début
    
    for i in range(num_threads):  # Crée num_threads threads
        t = threading.Thread(target=write_messages, args=(i,))  # Crée un thread qui exécutera write_messages avec l'ID i
        t.start()  # Démarre le thread
        threads.append(t)  # Ajoute le thread à la liste
    
    for t in threads:  # Parcourt tous les threads
        t.join()  # Attend que chaque thread se termine
    
    elapsed = time.perf_counter() - start_time  # Calcule le temps écoulé
    metrics = logger.get_metrics()  # Récupère les métriques de synchronisation du logger
    
    with open(log_file, 'r') as f:  # Ouvre le fichier de log en mode lecture
        lines = f.readlines()  # Lit toutes les lignes du fichier
    
    print(f"Nombre de threads : {num_threads}")  # Affiche le nombre de threads utilisés
    print(f"Accès concurrent maximum : {max_concurrent}")  # Affiche le nombre maximum d'accès simultanés
    print(f"Messages par thread : {messages_per_thread}")  # Affiche le nombre de messages par thread
    print(f"Total de lignes écrites : {len(lines)}")  # Affiche le nombre total de lignes écrites (devrait être 50)
    print(f"Temps écoulé : {elapsed:.4f}s")  # Affiche le temps écoulé
    print(f"Temps total passé en attente sur sémaphore : {metrics['total_semaphore_wait_time']:.4f}s")  # Affiche le temps d'attente sur sémaphore
    print(f"Nombre de contentions : {metrics['contention_count']}")  # Affiche le nombre de contentions
    print(f"Fichier créé : {log_file}")  # Affiche le nom du fichier créé
    print()  # Ligne vide pour la lisibilité


if __name__ == "__main__":  # Vérifie si le script est exécuté directement (pas importé)
    """
    Exécute toutes les démonstrations pour illustrer les concepts de synchronisation.
    
    Cette section est exécutée uniquement si le fichier est lancé directement.
    Elle exécute toutes les démonstrations dans l'ordre pour montrer :
    1. Les race conditions (problème)
    2. La correction avec Lock (solution)
    3. Les zones critiques avec fichiers
    4. L'utilisation de Sémaphores
    """
    print("\n" + "=" * 60)  # Affiche une ligne vide puis une ligne de séparation
    print("DÉMONSTRATIONS DE SYNCHRONISATION")  # Affiche le titre principal
    print("=" * 60 + "\n")  # Affiche une ligne de séparation puis une ligne vide
    
    # 1. Race condition sans verrou
    demonstrate_race_condition()  # Exécute la démonstration de race condition
    time.sleep(1)  # Attend 1 seconde avant la prochaine démonstration
    
    # 2. Correction avec Lock
    demonstrate_thread_safe_counter()  # Exécute la démonstration de compteur thread-safe
    time.sleep(1)  # Attend 1 seconde avant la prochaine démonstration
    
    # 3. Zone critique avec fichier
    demonstrate_critical_section_file()  # Exécute la démonstration de zone critique
    time.sleep(1)  # Attend 1 seconde avant la prochaine démonstration
    
    # 4. Sémaphore
    demonstrate_semaphore()  # Exécute la démonstration de sémaphore
    
    print("=" * 60)  # Affiche une ligne de séparation
    print("Toutes les démonstrations sont terminées!")  # Affiche le message de fin
    print("=" * 60)  # Affiche une ligne de séparation
