# src/synchronization_tools.py
"""
Module de synchronisation pour démontrer les concepts de parallélisme :
- Mutex (Lock)
- Sémaphore
- Variables partagées
- Mesure des temps d'attente sur verrous

Ce module fournit des classes et outils pour :
1. Démontrer les race conditions avec des compteurs non thread-safe
2. Corriger les race conditions avec des Lock (mutex)
3. Limiter l'accès concurrent avec des Sémaphores
4. Mesurer l'impact de la synchronisation sur les performances
5. Gérer la synchronisation entre processus (multiprocessing)

Toutes les classes incluent des métriques de synchronisation pour analyser
la contention et les temps d'attente sur les verrous.
"""
import threading  # Module pour la création et gestion de threads
import multiprocessing  # Module pour la création et gestion de processus
import time  # Module pour mesurer le temps (perf_counter pour haute précision)
from typing import Dict, Any  # Types pour les annotations de type
from collections import defaultdict  # Import non utilisé mais gardé pour compatibilité


class SynchronizationMetrics:
    """
    Collecte les métriques de synchronisation (temps d'attente, nombre de blocages).
    
    Cette classe permet de mesurer l'impact de la synchronisation sur les performances :
    - Temps passé en attente sur les verrous
    - Temps passé en attente sur les sémaphores
    - Nombre de contentions (fois où un thread/processus a dû attendre)
    - Nombre d'acquisitions de verrous/sémaphores
    """
    
    def __init__(self):
        """Initialise les conteneurs pour stocker les métriques de synchronisation"""
        self.lock_wait_times = []  # Liste pour stocker tous les temps d'attente sur les verrous
        self.semaphore_wait_times = []  # Liste pour stocker tous les temps d'attente sur les sémaphores
        self.lock_acquire_count = 0  # Compteur du nombre total d'acquisitions de verrous
        self.semaphore_acquire_count = 0  # Compteur du nombre total d'acquisitions de sémaphores
        self.contention_count = 0  # Compteur du nombre de fois où un thread/processus a dû attendre (temps > 0)
        
    def record_lock_wait(self, wait_time: float):
        """Enregistre le temps d'attente sur un verrou"""
        self.lock_wait_times.append(wait_time)  # Ajoute le temps d'attente à la liste
        if wait_time > 0:  # Si le temps d'attente est supérieur à 0, c'est une contention
            self.contention_count += 1  # Incrémente le compteur de contention
            
    def record_semaphore_wait(self, wait_time: float):
        """Enregistre le temps d'attente sur un sémaphore"""
        self.semaphore_wait_times.append(wait_time)  # Ajoute le temps d'attente à la liste
        if wait_time > 0:  # Si le temps d'attente est supérieur à 0, c'est une contention
            self.contention_count += 1  # Incrémente le compteur de contention
            
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de synchronisation calculées"""
        total_lock_wait = sum(self.lock_wait_times) if self.lock_wait_times else 0  # Somme tous les temps d'attente sur verrous
        total_semaphore_wait = sum(self.semaphore_wait_times) if self.semaphore_wait_times else 0  # Somme tous les temps d'attente sur sémaphores
        
        return {  # Retourne un dictionnaire avec toutes les statistiques
            "total_lock_wait_time": total_lock_wait,  # Temps total passé en attente sur les verrous
            "avg_lock_wait_time": total_lock_wait / len(self.lock_wait_times) if self.lock_wait_times else 0,  # Temps moyen d'attente sur les verrous
            "max_lock_wait_time": max(self.lock_wait_times) if self.lock_wait_times else 0,  # Temps maximum d'attente sur un verrou
            "total_semaphore_wait_time": total_semaphore_wait,  # Temps total passé en attente sur les sémaphores
            "avg_semaphore_wait_time": total_semaphore_wait / len(self.semaphore_wait_times) if self.semaphore_wait_times else 0,  # Temps moyen d'attente sur les sémaphores
            "lock_acquire_count": self.lock_acquire_count,  # Nombre total d'acquisitions de verrous
            "semaphore_acquire_count": self.semaphore_acquire_count,  # Nombre total d'acquisitions de sémaphores
            "contention_count": self.contention_count,  # Nombre total de contentions
            "total_wait_time": total_lock_wait + total_semaphore_wait  # Temps total d'attente (verrous + sémaphores)
        }


class ThreadSafeCounter:
    """
    Compteur thread-safe utilisant un Lock pour éviter les race conditions.
    
    Cette classe démontre comment protéger une variable partagée avec un mutex.
    Chaque opération d'incrémentation est protégée par un verrou, garantissant
    que seul un thread peut modifier la valeur à la fois.
    """
    
    def __init__(self, initial_value: int = 0):
        """Initialise le compteur avec une valeur de départ"""
        self._value = initial_value  # Valeur initiale du compteur (privée avec _)
        self._lock = threading.Lock()  # Crée un verrou pour protéger l'accès au compteur
        self._metrics = SynchronizationMetrics()  # Crée un objet pour collecter les métriques
        
    def increment(self) -> int:
        """Incrémente le compteur de manière thread-safe"""
        start_wait = time.perf_counter()  # Enregistre le temps avant d'essayer d'acquérir le verrou
        with self._lock:  # Acquiert le verrou (bloque si un autre thread l'a déjà)
            wait_time = time.perf_counter() - start_wait  # Calcule le temps d'attente pour acquérir le verrou
            self._metrics.record_lock_wait(wait_time)  # Enregistre le temps d'attente dans les métriques
            self._metrics.lock_acquire_count += 1  # Incrémente le compteur d'acquisitions
            self._value += 1  # Incrémente la valeur du compteur (zone critique protégée)
            return self._value  # Retourne la nouvelle valeur
            # Le verrou est automatiquement libéré à la sortie du bloc with
            
    def get(self) -> int:
        """Récupère la valeur actuelle du compteur de manière thread-safe"""
        with self._lock:  # Acquiert le verrou pour lire la valeur
            return self._value  # Retourne la valeur actuelle
            # Le verrou est automatiquement libéré à la sortie du bloc with
            
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de synchronisation collectées"""
        return self._metrics.get_stats()  # Retourne toutes les statistiques de synchronisation


class UnsafeCounter:
    """
    Compteur NON thread-safe pour démontrer les race conditions.
    
    Cette classe montre ce qui se passe quand plusieurs threads accèdent
    à une ressource partagée sans synchronisation. Les opérations ne sont
    pas atomiques, ce qui peut causer des pertes d'incrémentations.
    """
    
    def __init__(self, initial_value: int = 0):
        """Initialise le compteur avec une valeur de départ"""
        self._value = initial_value  # Valeur initiale du compteur (pas de protection)
        
    def increment(self) -> int:
        """Incrémente le compteur SANS protection (race condition possible)"""
        # Simulation d'une opération non atomique
        temp = self._value  # Lit la valeur actuelle dans une variable temporaire
        time.sleep(0.0001)  # Simule un délai de traitement (rend la race condition plus probable)
        self._value = temp + 1  # Écrit la nouvelle valeur (peut écraser les modifications d'autres threads)
        return self._value  # Retourne la nouvelle valeur (peut être incorrecte si plusieurs threads incrémentent)
        
    def get(self) -> int:
        """Récupère la valeur actuelle (peut être incorrecte en cas de race condition)"""
        return self._value  # Retourne la valeur actuelle sans protection


class ThreadSafeFileLogger:
    """
    Logger thread-safe utilisant un Lock pour écrire dans un fichier (zone critique).
    
    L'écriture dans un fichier est une zone critique car plusieurs threads
    peuvent essayer d'écrire simultanément, ce qui peut corrompre le fichier
    ou mélanger les lignes. Cette classe protège l'écriture avec un verrou.
    """
    
    def __init__(self, log_file: str):
        """Initialise le logger avec le chemin du fichier de log"""
        self.log_file = log_file  # Stocke le chemin du fichier de log
        self._lock = threading.Lock()  # Crée un verrou pour protéger l'écriture dans le fichier
        self._metrics = SynchronizationMetrics()  # Crée un objet pour collecter les métriques
        # Créer le fichier s'il n'existe pas
        with open(self.log_file, 'w') as f:  # Ouvre le fichier en mode écriture
            f.write("")  # Écrit une chaîne vide pour créer/initialiser le fichier
            
    def log(self, message: str):
        """Écrit un message dans le fichier de manière thread-safe"""
        start_wait = time.perf_counter()  # Enregistre le temps avant d'essayer d'acquérir le verrou
        with self._lock:  # Acquiert le verrou (bloque si un autre thread écrit déjà)
            wait_time = time.perf_counter() - start_wait  # Calcule le temps d'attente pour acquérir le verrou
            self._metrics.record_lock_wait(wait_time)  # Enregistre le temps d'attente dans les métriques
            self._metrics.lock_acquire_count += 1  # Incrémente le compteur d'acquisitions
            # Zone critique : écriture dans le fichier
            with open(self.log_file, 'a', encoding='utf-8') as f:  # Ouvre le fichier en mode append (ajout)
                f.write(f"{message}\n")  # Écrit le message suivi d'un saut de ligne
            # Le verrou est automatiquement libéré à la sortie du bloc with
                
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de synchronisation collectées"""
        return self._metrics.get_stats()  # Retourne toutes les statistiques de synchronisation


class SemaphoreFileLogger:
    """
    Logger utilisant un Sémaphore pour limiter le nombre de threads pouvant écrire simultanément.
    
    Contrairement au Lock qui n'autorise qu'un seul accès, le Sémaphore permet
    à N threads d'accéder simultanément à la ressource. Cela réduit la contention
    tout en contrôlant la charge sur la ressource.
    """
    
    def __init__(self, log_file: str, max_concurrent: int = 2):
        """Initialise le logger avec le chemin du fichier et le nombre max d'accès simultanés"""
        self.log_file = log_file  # Stocke le chemin du fichier de log
        self._semaphore = threading.Semaphore(max_concurrent)  # Crée un sémaphore autorisant max_concurrent accès simultanés
        self._metrics = SynchronizationMetrics()  # Crée un objet pour collecter les métriques
        # Créer le fichier s'il n'existe pas
        with open(self.log_file, 'w') as f:  # Ouvre le fichier en mode écriture
            f.write("")  # Écrit une chaîne vide pour créer/initialiser le fichier
            
    def log(self, message: str):
        """Écrit un message en utilisant un sémaphore pour limiter l'accès"""
        start_wait = time.perf_counter()  # Enregistre le temps avant d'essayer d'acquérir le sémaphore
        self._semaphore.acquire()  # Acquiert un permis du sémaphore (bloque si max_concurrent threads ont déjà le permis)
        try:  # Utilise try/finally pour garantir la libération du sémaphore même en cas d'erreur
            wait_time = time.perf_counter() - start_wait  # Calcule le temps d'attente pour acquérir le sémaphore
            self._metrics.record_semaphore_wait(wait_time)  # Enregistre le temps d'attente dans les métriques
            self._metrics.semaphore_acquire_count += 1  # Incrémente le compteur d'acquisitions
            # Zone critique : écriture dans le fichier (limitée par le sémaphore)
            with open(self.log_file, 'a', encoding='utf-8') as f:  # Ouvre le fichier en mode append (ajout)
                f.write(f"{message}\n")  # Écrit le message suivi d'un saut de ligne
        finally:  # Bloc exécuté dans tous les cas (succès ou erreur)
            self._semaphore.release()  # Libère le permis du sémaphore pour permettre à un autre thread d'écrire
            
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de synchronisation collectées"""
        return self._metrics.get_stats()  # Retourne toutes les statistiques de synchronisation


class ProcessSafeCounter:
    """
    Compteur process-safe utilisant multiprocessing.Value pour partager entre processus.
    
    Les processus ne partagent pas la mémoire comme les threads. Pour partager
    une variable entre processus, on utilise multiprocessing.Value qui crée
    une variable partagée en mémoire partagée.
    """
    
    def __init__(self, initial_value: int = 0):
        """Initialise le compteur avec une valeur de départ partagée entre processus"""
        self._value = multiprocessing.Value('i', initial_value)  # Crée une variable partagée de type entier ('i')
        self._lock = multiprocessing.Lock()  # Crée un verrou multiprocessing pour protéger l'accès
        self._metrics = SynchronizationMetrics()  # Crée un objet pour collecter les métriques
        
    def increment(self) -> int:
        """Incrémente le compteur de manière process-safe"""
        start_wait = time.perf_counter()  # Enregistre le temps avant d'essayer d'acquérir le verrou
        with self._lock:  # Acquiert le verrou multiprocessing (bloque si un autre processus l'a déjà)
            wait_time = time.perf_counter() - start_wait  # Calcule le temps d'attente pour acquérir le verrou
            self._metrics.record_lock_wait(wait_time)  # Enregistre le temps d'attente dans les métriques
            self._metrics.lock_acquire_count += 1  # Incrémente le compteur d'acquisitions
            self._value.value += 1  # Incrémente la valeur partagée (accès via .value)
            return self._value.value  # Retourne la nouvelle valeur
            # Le verrou est automatiquement libéré à la sortie du bloc with
            
    def get(self) -> int:
        """Récupère la valeur actuelle de manière process-safe"""
        with self._lock:  # Acquiert le verrou pour lire la valeur
            return self._value.value  # Retourne la valeur partagée (accès via .value)
            # Le verrou est automatiquement libéré à la sortie du bloc with
            
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de synchronisation collectées"""
        return self._metrics.get_stats()  # Retourne toutes les statistiques de synchronisation


class ProcessSafeFileLogger:
    """
    Logger process-safe utilisant un Lock multiprocessing pour écrire dans un fichier.
    
    L'écriture dans un fichier nécessite une synchronisation même entre processus,
    car plusieurs processus peuvent essayer d'écrire simultanément dans le même fichier.
    """
    
    def __init__(self, log_file: str):
        """Initialise le logger avec le chemin du fichier de log"""
        self.log_file = log_file  # Stocke le chemin du fichier de log
        self._lock = multiprocessing.Lock()  # Crée un verrou multiprocessing pour protéger l'écriture
        self._metrics = SynchronizationMetrics()  # Crée un objet pour collecter les métriques
        # Créer le fichier s'il n'existe pas
        with open(self.log_file, 'w') as f:  # Ouvre le fichier en mode écriture
            f.write("")  # Écrit une chaîne vide pour créer/initialiser le fichier
            
    def log(self, message: str):
        """Écrit un message dans le fichier de manière process-safe"""
        start_wait = time.perf_counter()  # Enregistre le temps avant d'essayer d'acquérir le verrou
        self._lock.acquire()  # Acquiert le verrou multiprocessing (bloque si un autre processus écrit déjà)
        try:  # Utilise try/finally pour garantir la libération du verrou même en cas d'erreur
            wait_time = time.perf_counter() - start_wait  # Calcule le temps d'attente pour acquérir le verrou
            self._metrics.record_lock_wait(wait_time)  # Enregistre le temps d'attente dans les métriques
            self._metrics.lock_acquire_count += 1  # Incrémente le compteur d'acquisitions
            # Zone critique : écriture dans le fichier
            with open(self.log_file, 'a', encoding='utf-8') as f:  # Ouvre le fichier en mode append (ajout)
                f.write(f"{message}\n")  # Écrit le message suivi d'un saut de ligne
        finally:  # Bloc exécuté dans tous les cas (succès ou erreur)
            self._lock.release()  # Libère le verrou pour permettre à un autre processus d'écrire
            
    def get_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques de synchronisation collectées"""
        return self._metrics.get_stats()  # Retourne toutes les statistiques de synchronisation
