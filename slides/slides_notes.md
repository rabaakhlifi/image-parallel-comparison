# Slides - Comparaison des approches de parallélisme avec synchronisation

## Slide 1 : Titre

**Titre** : Comparaison des approches de parallélisme en Python
**Sous-titre** : Synchronisation, Race Conditions, et Performance

---

## Slide 2 : Introduction

**Objectif du projet** :
- Comparer 5 approches de parallélisme
- Démontrer les concepts de synchronisation
- Mesurer l'impact des verrous sur les performances

**Cas d'usage** : Conversion d'images en niveaux de gris

---

## Slide 3 : Concepts de synchronisation

### Zone critique
- Section de code où plusieurs threads/processus accèdent à une ressource partagée
- Exemple : écriture dans un fichier log

### Race condition
- Accès simultané non synchronisé → résultats incorrects
- Démontré dans le projet avec compteurs et fichiers

### Mutex (Lock)
- Garantit l'exclusivité mutuelle
- Un seul thread/processus à la fois dans la zone critique

### Sémaphore
- Limite le nombre d'accès simultanés (N > 1)
- Moins de contention qu'un Lock strict

---

## Slide 4 : Architecture du projet

**Modules principaux** :
- `synchronization_tools.py` : Outils de synchronisation
- `processor.py` : Traitement d'images avec zone critique
- `versions/*.py` : Implémentations des différentes approches
- `measure.py` : Mesure des performances et métriques de synchronisation

**Expériences** :
1. Mono-thread (baseline)
2. Threading sans lock (race condition)
3. Threading avec lock (correction)
4. Threading avec semaphore
5. Multiprocessing avec lock
6. ThreadPoolExecutor avec lock/semaphore
7. ProcessPoolExecutor avec lock

---

## Slide 5 : Race Condition - Démonstration

**Problème** :
```
Thread 1 : lire valeur (100)
Thread 2 : lire valeur (100)
Thread 1 : incrémenter (101)
Thread 2 : incrémenter (101)
Résultat : 101 au lieu de 102 ❌
```

**Dans le projet** :
- Compteur non thread-safe perd des incrémentations
- Fichier log avec lignes mélangées
- Résultats imprévisibles

---

## Slide 6 : Correction avec Lock

**Solution** :
```python
with lock:
    # Zone critique protégée
    value += 1
    write_to_file()
```

**Résultat** :
- Accès exclusif garanti
- Résultats corrects ✅
- Mais coût en performance (contention)

---

## Slide 7 : Sémaphore - Limitation d'accès

**Principe** :
- Permet N accès simultanés (N > 1)
- Moins restrictif qu'un Lock
- Utile pour limiter la charge

**Exemple** :
```python
semaphore = Semaphore(2)  # 2 accès simultanés
with semaphore:
    write_to_file()
```

**Avantage** : Réduction de la contention par rapport à un Lock strict

---

## Slide 8 : GIL vs Multiprocessing

**Threading (avec GIL)** :
- GIL empêche l'exécution simultanée de code Python
- Limite la parallélisation CPU
- Mais verrous toujours nécessaires pour zones critiques

**Multiprocessing** :
- Pas de GIL → vraie parallélisation
- Chaque processus a sa propre mémoire
- Synchronisation nécessaire pour ressources partagées

---

## Slide 9 : Métriques mesurées

**Performance** :
- Temps total d'exécution
- Temps moyen par image
- Débit (images/seconde)

**Synchronisation** :
- Temps d'attente sur verrous
- Temps d'attente sur sémaphores
- Nombre de contentions
- Nombre d'acquisitions

---

## Slide 10 : Résultats attendus

**Observations typiques** :

1. **Mono-thread** : Baseline (référence)

2. **Threading sans lock** :
   - Plus rapide mais résultats incorrects ❌
   - Race conditions visibles

3. **Threading avec lock** :
   - Résultats corrects ✅
   - Légèrement plus lent (contention)

4. **Multiprocessing** :
   - Généralement le plus rapide pour CPU-bound
   - Pas de limitation par le GIL

---

## Slide 11 : Impact de la contention

**Facteurs** :
- Nombre de threads/processus
- Taille de la zone critique
- Fréquence d'accès

**Mesure** :
```
Contention = (Threads × Fréquence) / Temps_traitement
```

**Interprétation** :
- Contention < 1 : Peu de conflits
- Contention > 1 : Forte contention → optimiser

---

## Slide 12 : Bonnes pratiques

**Synchronisation** :
- ✅ Toujours protéger les zones critiques
- ✅ Minimiser la taille des zones critiques
- ✅ Choisir Lock vs Semaphore selon le besoin

**Performance** :
- ✅ CPU-bound → multiprocessing
- ✅ I/O-bound → threading
- ✅ Profiler avant d'optimiser

**Éviter** :
- ❌ Synchronisation excessive
- ❌ Verrous imbriqués
- ❌ Zones critiques trop grandes

---

## Slide 13 : Comparaison Lock vs Semaphore

**Lock (Mutex)** :
- Un seul accès à la fois
- Protection complète
- Contention potentiellement élevée

**Semaphore** :
- N accès simultanés
- Moins de contention si N bien choisi
- Meilleur débit pour certaines ressources

**Choix** : Dépend du besoin (exclusivité vs limitation)

---

## Slide 14 : Exemples de code

**Threading avec Lock** :
```python
lock = threading.Lock()
with lock:
    # Zone critique
    shared_resource += 1
```

**Threading avec Semaphore** :
```python
semaphore = threading.Semaphore(2)
semaphore.acquire()
try:
    # Zone critique (2 accès max)
    write_to_file()
finally:
    semaphore.release()
```

**Multiprocessing avec Lock** :
```python
lock = multiprocessing.Lock()
with lock:
    # Zone critique entre processus
    shared_file.write(data)
```

---

## Slide 15 : Leçons apprises

1. **Synchronisation nécessaire** : Les race conditions sont réelles et dangereuses

2. **Coût de la synchronisation** : Les verrous ont un impact sur les performances

3. **Mesurer avant d'optimiser** : Les métriques sont essentielles

4. **Choix de l'approche** : CPU-bound vs I/O-bound détermine l'approche

5. **Contention à minimiser** : Réduire la taille et la fréquence des zones critiques

---

## Slide 16 : Conclusion

**Points clés** :
- Synchronisation = nécessaire mais coûteuse
- Race conditions = problèmes réels à éviter
- Métriques = essentielles pour l'optimisation
- Choix d'approche = dépend du type de tâche

**Prochaines étapes** :
- Exécuter les expériences
- Analyser les résultats
- Optimiser selon les métriques

---

## Slide 17 : Questions

**Questions fréquentes** :
- Quand utiliser Lock vs Semaphore ?
- Comment minimiser la contention ?
- Threading vs Multiprocessing pour mon cas ?
- Comment mesurer l'impact des verrous ?

**Réponses dans** :
- Documentation du projet
- Code source commenté
- Résultats des expériences

---

## Slide 18 : Ressources

**Code source** :
- GitHub : [lien du projet]
- Documentation : `docs/README.md`
- Exemples : `src/examples_race_conditions.py`

**Références** :
- Python threading documentation
- Python multiprocessing documentation
- Concepts de synchronisation

**Contact** : [coordonnées]

