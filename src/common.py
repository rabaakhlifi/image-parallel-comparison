# src/common.py
import os
import time
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Crée les dossiers spécifiés s'ils n'existent pas déjà
def ensure_dirs(*paths):
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)

class Timer:
    # Initialise un chronomètre pour mesurer le temps d'exécution
    def __init__(self):
        self._t0 = None
        self.ticks = []

    # Démarre le chronomètre
    def start(self):
        self._t0 = time.perf_counter()

    # Arrête le chronomètre et retourne le temps écoulé
    def stop(self) -> float:
        if self._t0 is None:
            raise RuntimeError("Timer not started")
        elapsed = time.perf_counter() - self._t0
        self.ticks.append(elapsed)
        self._t0 = None
        return elapsed

# Liste tous les fichiers images dans un dossier (jpg, jpeg, png, bmp, tiff)
def list_images(folder: str) -> List[str]:
    p = Path(folder)
    exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    return [str(x) for x in p.iterdir() if x.suffix.lower() in exts]

# Sauvegarde des données au format JSON
def save_results_json(path: str, data: Dict[str, Any]):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Sauvegarde des données au format CSV avec en-têtes et lignes
def save_results_csv(path: str, headers: List[str], rows: List[List[Any]]):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

# Extrait le nom de fichier sécurisé depuis un chemin
def safe_filename(path: str) -> str:
    return str(Path(path).stem) + Path(path).suffix
