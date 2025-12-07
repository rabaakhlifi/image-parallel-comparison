# Comparaison des approches de parallélisme en Python avec synchronisation

## Introduction

Ce projet compare **5 approches de parallélisme** en Python pour un cas réel : la conversion en niveaux de gris d'un lot d'images, avec une **démonstration explicite des concepts de synchronisation**.

**Objectif** : mesurer les gains/pertes de performance et expliquer pourquoi certaines approches sont plus efficaces que d'autres, tout en démontrant les problèmes de **race conditions**, l'utilisation de **mutex (Lock)**, de **sémaphores**, et l'impact de la **contention** sur les performances.

## Concepts de synchronisation démontrés

### Zone critique

Une **zone critique** est une section de code où plusieurs threads ou processus accèdent à une ressource partagée. Dans ce projet, l'écriture dans un fichier log constitue une zone critique.

**Exemple dans le projet** :
- Écriture dans le fichier `processing.log` après chaque conversion d'image
- Incrémentation d'un compteur partagé
- Ajout d'éléments dans une liste partagée

### Race condition

Une **race condition** se produit lorsque plusieurs threads/processus accèdent simultanément à une ressource partagée sans synchronisation, ce qui peut causer des résultats incorrects ou imprévisibles.

**Démonstration dans le projet** :
- Version `threading_X_no_lock` : montre les race conditions
- Compteur non thread-safe qui perd des incrémentations
- Fichier log avec lignes mélangées ou corrompues

### Mutex (Lock)

Un **mutex (mutual exclusion)** ou **Lock** est un mécanisme de synchronisation qui garantit qu'un seul thread/processus peut accéder à une zone critique à la fois.

**Utilisation dans le projet** :
- `ThreadSafeFileLogger` : utilise `threading.Lock()` pour protéger l'écriture dans le fichier
- `ProcessSafeFileLogger` : utilise `multiprocessing.Lock()` pour protéger l'écriture entre processus
- Protection de l'ajout dans les listes partagées

### Sémaphore

Un **sémaphore** limite le nombre de threads/processus pouvant accéder simultanément à une ressource. Contrairement au Lock qui n'autorise qu'un seul accès, le sémaphore permet N accès simultanés.

**Utilisation dans le projet** :
- `SemaphoreFileLogger` : limite à 2 threads maximum pouvant écrire simultanément dans le log
- Permet de contrôler la charge sur les ressources partagées

### Contention

La **contention** se produit lorsque plusieurs threads/processus attendent pour acquérir un verrou. Cela peut ralentir significativement les performances.

**Mesure dans le projet** :
- Temps d'attente sur les verrous (`lock_wait_time`)
- Nombre de contentions (`contention_count`)
- Impact sur le temps total d'exécution

## Choix du sujet

Le traitement d'images est un cas d'usage intuitif (images → CPU) et représente souvent une tâche **CPU-bound**,
ce qui en fait un excellent exemple pour comparer différentes stratégies de parallélisme et de synchronisation.

## Architecture du projet

### Structure des fichiers

- **`src/processor.py`** : contient la fonction `convert_to_grayscale` qui charge une image avec Pillow
  et la convertit en niveaux de gris via `ImageOps.grayscale`. Inclut une zone critique (écriture log).

- **`src/synchronization_tools.py`** : module dédié aux outils de synchronisation :
  - `ThreadSafeCounter` : compteur thread-safe avec Lock
  - `UnsafeCounter` : compteur non thread-safe (démonstration race condition)
  - `ThreadSafeFileLogger` : logger avec Lock
  - `SemaphoreFileLogger` : logger avec Sémaphore
  - `ProcessSafeFileLogger` : logger pour multiprocessing
  - `SynchronizationMetrics` : collecte des métriques de synchronisation

- **`src/examples_race_conditions.py`** : démonstrations pédagogiques des race conditions et leur correction

- **`src/versions/*.py`** : implémentations des différentes variantes de parallélisme :
  - `mono.py` : séquentiel (baseline)
  - `threading_version.py` : threading avec/sans lock, avec semaphore
  - `multiprocessing_version.py` : multiprocessing avec synchronisation
  - `threadpool_executor.py` : ThreadPoolExecutor avec synchronisation
  - `processpool_executor.py` : ProcessPoolExecutor avec synchronisation

- **`src/runner.py`** : orchestre les expériences et sauvegarde les résultats

- **`src/measure.py`** : mesure les performances incluant les métriques de synchronisation

- **`src/common.py`** : utilitaires communs (timers, sauvegarde, etc.)

## Comparaison détaillée

Le projet compare les approches suivantes :

1. **Mono-thread** : implémentation séquentielle (baseline, aucune synchronisation nécessaire)

2. **Threading sans lock** : démontre les race conditions
   - Accès non synchronisé aux ressources partagées
   - Résultats incorrects possibles

3. **Threading avec Lock** : correction avec mutex
   - Protection des zones critiques
   - Mesure du temps d'attente sur verrous

4. **Threading avec Semaphore** : limitation d'accès concurrent
   - Contrôle du nombre de threads accédant simultanément à une ressource

5. **Multiprocessing avec Lock** : synchronisation entre processus
   - Utilisation de `multiprocessing.Lock()`
   - Pas de GIL, vraie parallélisation

6. **ThreadPoolExecutor avec Lock** : API moderne avec synchronisation

7. **ThreadPoolExecutor avec Semaphore** : limitation d'accès avec API moderne

8. **ProcessPoolExecutor avec Lock** : processus avec synchronisation

## Problèmes rencontrés

### Global Interpreter Lock (GIL)

Le GIL limite l'efficacité des threads pour les tâches **CPU-bound**, car il empêche l'exécution simultanée de code Python sur plusieurs cœurs. Cependant, les verrous sont toujours nécessaires pour protéger les zones critiques (fichiers, variables partagées).

### Race conditions

Sans synchronisation, plusieurs threads peuvent modifier simultanément une ressource partagée, causant :
- Perte de données (incrémentations manquées)
- Corruption de fichiers
- Résultats imprévisibles

### Contention sur les verrous

L'utilisation excessive de verrous peut créer de la contention :
- Plusieurs threads attendent pour acquérir le même verrou
- Temps d'attente qui s'accumule
- Impact négatif sur les performances

### Pickling et multiprocessing

Les objets non picklables peuvent causer des erreurs avec `ProcessPoolExecutor`, qui nécessite de sérialiser les arguments et les résultats. Les verrous doivent être partagés via `multiprocessing.Manager()` ou `multiprocessing.Value()`.

### I/O vs CPU-bound

Il est crucial de différencier les tâches I/O-bound des tâches CPU-bound avant d'opter pour threads ou processus, et de choisir la bonne stratégie de synchronisation.

## Solutions et bonnes pratiques

### Synchronisation appropriée

- **Pour les zones critiques** : toujours utiliser un Lock ou un mécanisme de synchronisation
- **Pour limiter l'accès** : utiliser un Semaphore au lieu d'un Lock si plusieurs accès simultanés sont acceptables
- **Pour multiprocessing** : utiliser `multiprocessing.Lock()` ou `multiprocessing.Manager()`

### Minimiser la contention

- Réduire la taille des zones critiques
- Éviter les verrous imbriqués
- Utiliser des structures de données thread-safe quand possible
- Profiler pour identifier les goulots d'étranglement

### Pour les tâches CPU-bound

- Utiliser `multiprocessing` (pas de GIL)
- Utiliser des extensions C
- Utiliser NumPy vectorisé
- Utiliser Cython

### Pour les tâches I/O-bound

- Utiliser `threading` (GIL libéré pendant les I/O)
- Utiliser `async IO`
- Synchronisation minimale nécessaire

### Autres recommandations

- Éviter les gros objets non picklables dans les arguments de `ProcessPool`
- Choisir la bonne approche selon le type de tâche
- Mesurer l'impact des verrous sur les performances
- Documenter les zones critiques dans le code

## Métriques mesurées

Le projet mesure :

- **Temps total** : temps d'exécution complet
- **Temps moyen par image** : temps moyen de traitement
- **Débit** : images par seconde
- **Temps d'attente sur verrous** : temps passé en attente pour acquérir un Lock
- **Temps d'attente sur sémaphores** : temps passé en attente pour acquérir un Semaphore
- **Nombre de contentions** : nombre de fois où un thread/processus a dû attendre
- **Nombre d'acquisitions** : nombre de fois où un verrou/sémaphore a été acquis

## Conclusion

Les tests empiriques sont plus fiables que les conseils génériques.
Ce projet vous permet d'exécuter des tests réels sur votre machine et de mesurer concrètement :
- Les performances de chaque approche de parallélisme
- L'impact des race conditions
- Le coût de la synchronisation (verrous, sémaphores)
- La différence entre threading et multiprocessing pour les tâches CPU-bound
- L'importance de la synchronisation appropriée
