# Script vidéo - Démonstration du projet de parallélisme avec synchronisation

## Introduction (0:00 - 1:00)

**[Présentation]**

Bonjour ! Aujourd'hui, je vais vous présenter un projet de comparaison des approches de parallélisme en Python, avec une démonstration explicite des concepts de synchronisation : les race conditions, les mutex, les sémaphores, et leur impact sur les performances.

**[Contexte]**

Le projet traite un cas réel : la conversion d'images en niveaux de gris. Mais au-delà de la simple comparaison de performance, nous allons voir comment gérer correctement les ressources partagées et éviter les problèmes de concurrence.

---

## Partie 1 : Concepts de synchronisation (1:00 - 3:00)

**[Zone critique]**

Commençons par comprendre ce qu'est une zone critique. Dans notre projet, l'écriture dans un fichier log après chaque conversion d'image constitue une zone critique. C'est une section de code où plusieurs threads ou processus peuvent accéder simultanément à une ressource partagée.

**[Race condition]**

Sans synchronisation, cela peut causer une race condition. Regardons un exemple simple : plusieurs threads incrémentent un compteur en même temps. Sans protection, certaines incrémentations peuvent être perdues, et le résultat final est incorrect.

**[Démonstration code]**

Je vais vous montrer le code dans `examples_race_conditions.py` qui démontre ce problème.

---

## Partie 2 : Correction avec Lock (3:00 - 5:00)

**[Mutex/Lock]**

Pour corriger ce problème, nous utilisons un mutex, aussi appelé Lock. Un mutex garantit qu'un seul thread ou processus peut accéder à la zone critique à la fois.

**[Code avec Lock]**

Voici comment nous l'utilisons dans le projet. Le `ThreadSafeFileLogger` utilise un `threading.Lock()` pour protéger l'écriture dans le fichier. Chaque thread doit acquérir le verrou avant d'écrire, et le libérer après.

**[Impact sur performance]**

Mais attention : cette protection a un coût. Les threads doivent attendre leur tour, ce qui crée de la contention. Nous mesurons ce temps d'attente dans nos expériences.

---

## Partie 3 : Sémaphore (5:00 - 6:30)

**[Sémaphore]**

Parfois, un Lock est trop restrictif. Un sémaphore permet à N threads ou processus d'accéder simultanément à une ressource, où N peut être supérieur à 1.

**[Utilisation dans le projet]**

Dans notre projet, le `SemaphoreFileLogger` limite à 2 threads maximum pouvant écrire simultanément dans le log. Cela réduit la contention par rapport à un Lock strict, tout en contrôlant la charge sur la ressource.

**[Comparaison]**

Nous comparons les performances avec et sans sémaphore pour voir l'impact.

---

## Partie 4 : Architecture du projet (6:30 - 8:00)

**[Structure]**

Regardons la structure du projet. Le module `synchronization_tools.py` contient tous nos outils de synchronisation : compteurs thread-safe, loggers avec Lock ou Semaphore, et la collecte de métriques.

**[Versions]**

Dans `src/versions/`, nous avons les différentes implémentations :
- Mono-thread : baseline séquentielle
- Threading sans lock : démontre les race conditions
- Threading avec lock : correction
- Threading avec semaphore : limitation d'accès
- Multiprocessing : synchronisation entre processus
- ThreadPoolExecutor et ProcessPoolExecutor : API modernes

**[Runner]**

Le fichier `runner.py` orchestre toutes ces expériences et génère les résultats.

---

## Partie 5 : Exécution et résultats (8:00 - 11:00)

**[Lancement]**

Lançons les expériences. Je vais exécuter le script avec différentes configurations pour comparer les approches.

**[Observation des résultats]**

Regardons les résultats. Nous voyons que :
1. La version sans lock est plus rapide mais produit des résultats incorrects
2. La version avec lock est correcte mais plus lente à cause de la contention
3. La version avec semaphore offre un bon compromis
4. Multiprocessing est généralement le plus rapide pour les tâches CPU-bound

**[Métriques de synchronisation]**

Les métriques de synchronisation nous montrent :
- Le temps passé en attente sur les verrous
- Le nombre de contentions
- L'impact sur le temps total

---

## Partie 6 : Analyse et leçons (11:00 - 13:00)

**[Analyse de la contention]**

Analysons la contention. Quand plusieurs threads se disputent le même verrou, le temps d'attente s'accumule. C'est pourquoi il est important de minimiser la taille des zones critiques.

**[GIL vs Multiprocessing]**

Pour les tâches CPU-bound, le GIL limite l'efficacité du threading. Multiprocessing permet une vraie parallélisation, mais nécessite une synchronisation appropriée pour les ressources partagées.

**[Bonnes pratiques]**

Voici les bonnes pratiques que nous avons apprises :
- Toujours synchroniser les zones critiques
- Minimiser la taille des zones critiques
- Choisir Lock vs Semaphore selon le besoin
- Profiler avant d'optimiser
- Mesurer l'impact des verrous

---

## Partie 7 : Démonstration pratique (13:00 - 15:00)

**[Exemple de race condition]**

Je vais vous montrer un exemple concret de race condition. Regardons le compteur non thread-safe qui perd des incrémentations.

**[Correction]**

Maintenant, la version avec Lock qui garantit des résultats corrects.

**[Comparaison visuelle]**

Comparons visuellement les fichiers log générés : celui sans lock a des lignes mélangées, celui avec lock est propre.

---

## Conclusion (15:00 - 16:00)

**[Résumé]**

Pour résumer, ce projet démontre :
- L'importance de la synchronisation
- Les problèmes des race conditions
- L'impact des verrous sur les performances
- La différence entre threading et multiprocessing
- L'utilisation appropriée des Lock et Semaphore

**[Points clés]**

Les points clés à retenir :
1. La synchronisation est nécessaire mais coûteuse
2. Les race conditions sont des problèmes réels
3. Les métriques sont essentielles pour l'optimisation
4. Le choix d'approche dépend du type de tâche

**[Prochaines étapes]**

Vous pouvez maintenant :
- Exécuter les expériences vous-même
- Analyser les résultats
- Expérimenter avec différentes configurations
- Lire la documentation complète dans `docs/`

**[Fin]**

Merci d'avoir regardé ! N'hésitez pas à explorer le code source et à poser des questions. À bientôt !

---

## Notes pour l'enregistrement

**Timing** : Environ 16 minutes au total

**Sections à filmer** :
1. Introduction et concepts (diapositives)
2. Code source (IDE)
3. Exécution des expériences (terminal)
4. Analyse des résultats (fichiers JSON/CSV)
5. Démonstration pratique (exemples de code)

**Points d'attention** :
- Montrer clairement les race conditions dans le code
- Expliquer chaque concept avant de le démontrer
- Comparer visuellement les résultats
- Utiliser des graphiques si possible pour les métriques

**Outils nécessaires** :
- IDE avec coloration syntaxique
- Terminal pour exécution
- Visualisation des résultats (JSON viewer, CSV viewer)
- Éditeur de texte pour montrer le code

