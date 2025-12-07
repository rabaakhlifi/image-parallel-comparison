# src/versions/mono.py
"""
Version séquentielle (mono-thread) - Baseline sans parallélisme.

Ce module implémente le traitement séquentiel des images, c'est-à-dire
une image après l'autre, sans parallélisme. Cette version sert de baseline
pour comparer les performances des autres approches.

Rôle détaillé :
- Traite les images une par une dans une boucle
- Aucune synchronisation nécessaire (pas de partage de ressources)
- Mesure le temps total et le temps par image
- Retourne les statistiques de traitement
- Utilisé comme référence pour comparer les gains de performance

Aucune race condition possible car :
- Une seule image est traitée à la fois
- Pas de threads ou processus concurrents
- Pas de ressources partagées
"""
from typing import List, Dict  # Types pour les annotations de type
from pathlib import Path  # Import de Path (non utilisé directement mais gardé pour cohérence)
from ..processor import convert_to_grayscale  # Import de la fonction de conversion d'images
from ..common import Timer  # Import de la classe Timer pour mesurer le temps


# Traite les images de manière séquentielle (une par une, sans parallélisme)
def process_sequential(image_paths: List[str], output_dir: str) -> Dict:
    """
    Traite les images de manière séquentielle.
    
    Aucune synchronisation nécessaire car :
    - Une seule image est traitée à la fois
    - Pas de partage de ressources entre threads/processus
    - Pas de race condition possible
    
    Args:
        image_paths: Liste des chemins vers les images
        output_dir: Dossier de sortie
    
    Returns:
        Dictionnaire avec les statistiques de traitement
    """
    timer = Timer()  # Crée un chronomètre pour mesurer le temps total
    stats = {"runs": []}  # Initialise le dictionnaire de statistiques avec une liste vide pour les résultats individuels
    timer.start()  # Démarre le chronomètre pour mesurer le temps total de traitement
    
    for p in image_paths:  # Parcourt chaque image dans la liste
        t = Timer()  # Crée un nouveau chronomètre pour mesurer le temps de traitement de cette image
        t.start()  # Démarre le chronomètre pour cette image
        res = convert_to_grayscale(p, output_dir, use_lock=False)  # Convertit l'image (use_lock=False car pas de threads)
        elapsed = t.stop()  # Arrête le chronomètre et récupère le temps écoulé pour cette image
        stats["runs"].append({  # Ajoute les informations de traitement de cette image à la liste
            "image": p,  # Chemin de l'image traitée
            "elapsed": elapsed,  # Temps écoulé pour traiter cette image
            "success": res.get("success", False),  # Indique si la conversion a réussi (valeur par défaut: False)
            "processing_time": res.get("processing_time", elapsed)  # Temps de traitement depuis le résultat (ou elapsed si absent)
        })
    
    total = timer.stop()  # Arrête le chronomètre principal et récupère le temps total
    stats.update({  # Met à jour le dictionnaire de statistiques avec les informations globales
        "total_time": total,  # Temps total de traitement de toutes les images
        "n_images": len(image_paths),  # Nombre total d'images traitées
        "sync_metrics": {}  # Pas de métriques de synchronisation en séquentiel (dictionnaire vide)
    })
    return stats  # Retourne le dictionnaire complet avec toutes les statistiques
