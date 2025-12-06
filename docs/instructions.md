# Instructions d'installation et d'utilisation

Ce guide vous explique comment installer et lancer le projet de comparaison des approches de parallélisme en Python.

## Prérequis

- **Python 3.7 ou supérieur** installé sur votre système
- Un terminal/invite de commande

### Vérifier l'installation de Python

```bash
python --version
```

ou

```bash
python3 --version
```

## Installation

### 1. Cloner ou télécharger le projet

Si vous avez cloné le projet depuis un dépôt Git, vous êtes déjà prêt. Sinon, assurez-vous d'avoir tous les fichiers du projet dans un dossier.

### 2. Créer un environnement virtuel (recommandé)

Il est recommandé d'utiliser un environnement virtuel pour isoler les dépendances du projet.

**Sur Windows :**

```bash
python -m venv venv
# ou py -m venv venv si python n'a pas fonctionné
venv\Scripts\activate
```

**Sur Linux/Mac :**

```bash
python3 -m venv venv
source venv/bin/activate
```

Une fois activé, vous devriez voir `(venv)` au début de votre ligne de commande.

### 3. Installer les dépendances

Les dépendances nécessaires sont :

- **Pillow** : pour le traitement d'images
- **psutil** : pour le monitoring des performances (optionnel)

Installez-les avec pip :

```bash
pip install Pillow psutil
```

ou si vous avez un fichier `requirements.txt` :

```bash
pip install -r requirements.txt
```

## Préparation des images

### 1. Créer le dossier d'images

Assurez-vous d'avoir un dossier `images` à la racine du projet contenant vos images à traiter.

**Formats supportés :** `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`

### 2. Ajouter des images

Placez vos images dans le dossier `images/`. Le projet traitera automatiquement toutes les images trouvées dans ce dossier.

## Lancement du projet

### Commande de base

Depuis la racine du projet, lancez :

```bash
python -m src.runner
```

ou

```bash
python src/runner.py
```

### Options de configuration

Le script accepte plusieurs arguments pour personnaliser l'exécution :

```bash
python -m src.runner --images ./images --output ./output --results ./results --threads 2 4 8 --processes 2 4
```

**Arguments disponibles :**

- `--images` : Dossier contenant les images à traiter (défaut: `../images`)
- `--output` : Dossier où sauvegarder les images converties (défaut: `../output`)
- `--results` : Dossier où sauvegarder les résultats de performance (défaut: `../results`)
- `--threads` : Nombre de threads à tester (défaut: `2 4 8`)
- `--processes` : Nombre de processus à tester (défaut: `2 4`)

**Exemple avec des valeurs personnalisées :**

```bash
python -m src.runner --images ./images --output ./output --results ./results --threads 4 8 --processes 4
```

## Résultats

Après l'exécution, vous trouverez :

1. **Images converties** dans le dossier `output/` :

   - `mono/` : images traitées de manière séquentielle
   - `threading_X/` : images traitées avec X threads
   - `multiproc_X/` : images traitées avec X processus
   - `threadpool_X/` : images traitées avec ThreadPoolExecutor (X workers)
   - `processpool_X/` : images traitées avec ProcessPoolExecutor (X workers)

2. **Résultats de performance** dans le dossier `results/` :
   - Fichiers JSON détaillés pour chaque approche
   - Fichiers CSV avec les métriques principales
   - `summary.json` : résumé comparatif de toutes les approches

## Désactiver l'environnement virtuel

Une fois terminé, vous pouvez désactiver l'environnement virtuel :

```bash
deactivate
```

## Dépannage

### Erreur : "Aucune image trouvée"

Assurez-vous que :

- Le dossier `images/` existe
- Il contient des images aux formats supportés (`.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`)
- Vous avez spécifié le bon chemin avec `--images` si nécessaire

### Erreur : "Module not found"

Vérifiez que :

- L'environnement virtuel est activé
- Les dépendances sont installées : `pip install Pillow psutil`
- Vous êtes dans le bon répertoire (racine du projet)

### Erreur : "Permission denied" (Linux/Mac)

Si vous avez des problèmes de permissions, vous pouvez utiliser :

```bash
chmod +x src/runner.py
```

## Exemple complet

Voici un exemple complet de commandes pour une première utilisation :

```bash
# 1. Créer l'environnement virtuel
python -m venv venv

# 2. Activer l'environnement virtuel
# Windows :
venv\Scripts\activate
# Linux/Mac :
source venv/bin/activate

# 3. Installer les dépendances
pip install Pillow psutil

# 4. Vérifier que vous avez des images dans le dossier images/
# (ajoutez-en si nécessaire)

# 5. Lancer le projet
python -m src.runner

# 6. Consulter les résultats dans les dossiers output/ et results/
```

## Support

Pour plus d'informations sur le projet, consultez le fichier `README.md` dans le dossier `docs/`.
