# Comparaison des approches de parallélisme en Python

## Introduction

Ce projet compare **5 approches de parallélisme** en Python pour un cas réel : la conversion en niveaux de gris d'un lot d'images.

**Objectif** : mesurer les gains/pertes de performance et expliquer pourquoi certaines approches sont plus efficaces que d'autres.

## Choix du sujet

Le traitement d'images est un cas d'usage intuitif (images → CPU) et représente souvent une tâche **CPU-bound**,
ce qui en fait un excellent exemple pour comparer différentes stratégies de parallélisme.

## Architecture du projet

_(Voir l'arborescence fournie plus haut)_

### Structure des fichiers

- **`src/processor.py`** : contient la fonction `convert_to_grayscale` qui charge une image avec Pillow
  et la convertit en niveaux de gris via `ImageOps.grayscale`
- **`src/versions/*.py`** : implémentations des différentes variantes de parallélisme
- **`src/runner.py`** : orchestre les expériences et sauvegarde les résultats

## Comparaison détaillée

Le projet compare les approches suivantes :

1. **Mono-thread** : implémentation séquentielle (baseline)
2. **Threading** : création de threads et utilisation de queues
3. **Multiprocessing** : utilisation de `multiprocessing.Pool`
4. **ThreadPoolExecutor** : API `concurrent.futures` avec threads
5. **ProcessPoolExecutor** : API `concurrent.futures` avec processus

## Problèmes rencontrés

### Global Interpreter Lock (GIL)

Le GIL limite l'efficacité des threads pour les tâches **CPU-bound**, car il empêche l'exécution simultanée de code Python sur plusieurs cœurs.

### Pickling

Les objets non picklables peuvent causer des erreurs avec `ProcessPoolExecutor`, qui nécessite de sérialiser les arguments et les résultats.

### I/O vs CPU-bound

Il est crucial de différencier les tâches I/O-bound des tâches CPU-bound avant d'opter pour threads ou processus.

## Solutions et bonnes pratiques

### Profiling avant optimisation

Toujours profiler le code avant d'optimiser pour identifier les vrais goulots d'étranglement.

### Pour les tâches CPU-bound

- Utiliser `multiprocessing`
- Utiliser des extensions C
- Utiliser NumPy vectorisé
- Utiliser Cython

### Pour les tâches I/O-bound

- Utiliser `threading`
- Utiliser `async IO`

### Autres recommandations

- Éviter les gros objets non picklables dans les arguments de `ProcessPool`
- Choisir la bonne approche selon le type de tâche

## Conclusion

Les tests empiriques sont plus fiables que les conseils génériques.
Ce projet vous permet d'exécuter des tests réels sur votre machine et de mesurer concrètement les performances de chaque approche.
