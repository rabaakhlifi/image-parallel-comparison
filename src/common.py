# src/common.py
"""
Module commun avec utilitaires pour le projet.

Ce module fournit des fonctions et classes utilitaires utilisées dans tout le projet :
- Gestion des dossiers (création automatique)
- Mesure du temps d'exécution (Timer)
- Liste des fichiers images dans un dossier
- Sauvegarde des résultats au format JSON et CSV
- Extraction de noms de fichiers sécurisés

Rôle détaillé :
- Fonctions réutilisables pour éviter la duplication de code
- Classes utilitaires pour la mesure de performance
- Gestion des fichiers et dossiers
- Formatage et export des données
"""
import os  # Module pour les opérations sur le système de fichiers
import time  # Module pour mesurer le temps (perf_counter pour haute précision)
import json  # Module pour la sérialisation/désérialisation JSON
import csv  # Module pour la lecture/écriture de fichiers CSV
from pathlib import Path  # Import de Path pour la manipulation de chemins de fichiers
from typing import List, Dict, Any, Tuple  # Types pour les annotations de type


# Crée les dossiers spécifiés s'ils n'existent pas déjà
def ensure_dirs(*paths):
    """
    Crée les dossiers spécifiés s'ils n'existent pas déjà.
    
    Cette fonction prend un nombre variable d'arguments (chemins de dossiers)
    et crée chaque dossier s'il n'existe pas. La création est récursive
    (parents=True) pour créer tous les dossiers parents nécessaires.
    """
    for p in paths:  # Parcourt chaque chemin fourni
        Path(p).mkdir(parents=True, exist_ok=True)  # Crée le dossier (récursif) s'il n'existe pas (pas d'erreur si existe déjà)


class Timer:
    """
    Chronomètre pour mesurer le temps d'exécution.
    
    Cette classe permet de mesurer précisément le temps d'exécution d'opérations.
    Elle utilise time.perf_counter() pour une haute précision et peut enregistrer
    plusieurs mesures (ticks) pour calculer des statistiques.
    """
    
    # Initialise un chronomètre pour mesurer le temps d'exécution
    def __init__(self):
        """Initialise le chronomètre avec des valeurs par défaut"""
        self._t0 = None  # Temps de début (None si le chronomètre n'est pas démarré)
        self.ticks = []  # Liste pour stocker tous les temps mesurés (historique)

    # Démarre le chronomètre
    def start(self):
        """Démarre le chronomètre en enregistrant le temps actuel"""
        self._t0 = time.perf_counter()  # Enregistre le temps actuel avec haute précision

    # Arrête le chronomètre et retourne le temps écoulé
    def stop(self) -> float:
        """
        Arrête le chronomètre et retourne le temps écoulé.
        
        Calcule la différence entre le temps actuel et le temps de début,
        ajoute cette mesure à l'historique, et réinitialise le chronomètre.
        """
        if self._t0 is None:  # Vérifie si le chronomètre a été démarré
            raise RuntimeError("Timer not started")  # Lève une erreur si le chronomètre n'a pas été démarré
        elapsed = time.perf_counter() - self._t0  # Calcule le temps écoulé (temps actuel - temps de début)
        self.ticks.append(elapsed)  # Ajoute cette mesure à l'historique
        self._t0 = None  # Réinitialise le chronomètre (None pour indiquer qu'il est arrêté)
        return elapsed  # Retourne le temps écoulé en secondes


# Liste tous les fichiers images dans un dossier (jpg, jpeg, png, bmp, tiff)
def list_images(folder: str) -> List[str]:
    """
    Liste tous les fichiers images dans un dossier (jpg, jpeg, png, bmp, tiff).
    
    Cette fonction parcourt un dossier et retourne la liste des chemins complets
    de tous les fichiers images trouvés. Les extensions sont vérifiées en
    minuscules pour être insensible à la casse.
    """
    p = Path(folder)  # Convertit le chemin du dossier en objet Path
    exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}  # Ensemble des extensions d'images supportées
    return [str(x) for x in p.iterdir() if x.suffix.lower() in exts]  # Retourne la liste des chemins (en string) des fichiers dont l'extension est dans exts


# Sauvegarde des données au format JSON
def save_results_json(path: str, data: Dict[str, Any]):
    """
    Sauvegarde des données au format JSON.
    
    Cette fonction écrit un dictionnaire Python dans un fichier JSON avec
    indentation pour la lisibilité et support des caractères Unicode.
    """
    with open(path, 'w', encoding='utf-8') as f:  # Ouvre le fichier en mode écriture avec encodage UTF-8
        json.dump(data, f, indent=2, ensure_ascii=False)  # Écrit le dictionnaire en JSON (indenté, avec caractères Unicode)


# Sauvegarde des données au format CSV avec en-têtes et lignes
def save_results_csv(path: str, headers: List[str], rows: List[List[Any]]):
    """
    Sauvegarde des données au format CSV avec en-têtes et lignes.
    
    Cette fonction écrit un fichier CSV avec une ligne d'en-têtes suivie
    des lignes de données. Utilise le module csv pour gérer correctement
    l'échappement des caractères spéciaux.
    """
    with open(path, 'w', newline='', encoding='utf-8') as f:  # Ouvre le fichier en mode écriture (newline='' pour compatibilité Windows)
        writer = csv.writer(f)  # Crée un writer CSV
        writer.writerow(headers)  # Écrit la ligne d'en-têtes
        writer.writerows(rows)  # Écrit toutes les lignes de données


# Extrait le nom de fichier sécurisé depuis un chemin
def safe_filename(path: str) -> str:
    """
    Extrait le nom de fichier sécurisé depuis un chemin.
    
    Cette fonction extrait le nom de fichier (sans le chemin) depuis un chemin complet.
    Retourne le nom de base (stem) + l'extension (suffix).
    """
    return str(Path(path).stem) + Path(path).suffix  # Retourne le nom de base + extension (sans le chemin)
