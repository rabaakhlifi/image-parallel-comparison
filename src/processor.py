# src/processor.py
"""
Module de traitement d'images avec zone critique pour démontrer la synchronisation.

Ce module contient la fonction principale de conversion d'images en niveaux de gris.
La conversion d'image est combinée avec l'écriture dans un fichier log, qui constitue
une zone critique nécessitant une synchronisation si plusieurs threads/processus
y accèdent simultanément.

Rôle détaillé :
- Charge une image avec la bibliothèque Pillow
- Convertit l'image en niveaux de gris
- Sauvegarde l'image convertie
- Écrit dans un fichier log (zone critique) avec ou sans synchronisation
- Gère les erreurs et les tracebacks
- Mesure le temps de traitement de chaque image
"""
from PIL import Image, ImageOps  # Import de Pillow pour le traitement d'images
from pathlib import Path  # Import de Path pour la manipulation de chemins de fichiers
import traceback  # Import pour capturer et formater les traces d'erreur
import time  # Import pour mesurer le temps d'exécution
from typing import Optional  # Type pour les paramètres optionnels


# Variable globale pour le logger (sera partagée entre threads/processus)
_global_logger = None  # Variable globale qui stockera le logger partagé (initialisée à None)


def set_global_logger(logger):
    """
    Définit le logger global pour toutes les conversions.
    
    Cette fonction permet de partager un logger entre tous les threads/processus
    qui appellent convert_to_grayscale. Le logger doit être thread-safe ou
    process-safe selon le contexte d'utilisation.
    """
    global _global_logger  # Déclare qu'on modifie la variable globale
    _global_logger = logger  # Assigne le logger passé en paramètre à la variable globale


def convert_to_grayscale(
    input_path: str,  # Chemin vers l'image source à convertir
    output_dir: str,  # Dossier où sauvegarder l'image convertie
    suffix="_gray",  # Suffixe à ajouter au nom de fichier (par défaut "_gray")
    thread_id: Optional[str] = None,  # Identifiant du thread/processus (optionnel, pour le log)
    use_lock: bool = True  # Si True, utilise le logger thread-safe (avec lock)
) -> dict:  # Retourne un dictionnaire avec les informations de traitement
    """
    Convertit une image en niveaux de gris et la sauvegarde dans le dossier de sortie.
    
    Zone critique : L'écriture dans le fichier log est une zone critique qui nécessite
    une synchronisation si plusieurs threads/processus y accèdent simultanément.
    
    Args:
        input_path: Chemin vers l'image source
        output_dir: Dossier de sortie
        suffix: Suffixe à ajouter au nom de fichier
        thread_id: Identifiant du thread/processus (pour le log)
        use_lock: Si True, utilise le logger thread-safe (avec lock)
    
    Returns:
        Dictionnaire avec les informations de traitement
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)  # Crée le dossier de sortie s'il n'existe pas (création récursive)
    in_path = Path(input_path)  # Convertit le chemin d'entrée en objet Path
    out_name = in_path.stem + suffix + in_path.suffix  # Construit le nom de fichier de sortie (nom_base + suffixe + extension)
    out_path = Path(output_dir) / out_name  # Construit le chemin complet de sortie (dossier + nom_fichier)
    
    start_time = time.perf_counter()  # Enregistre le temps de début du traitement (haute précision)
    
    try:  # Bloc try pour capturer les erreurs
        # Traitement de l'image (opération CPU-bound)
        with Image.open(in_path) as img:  # Ouvre l'image avec Pillow (gestion automatique de la fermeture)
            gray = ImageOps.grayscale(img)  # Convertit l'image en niveaux de gris
            gray.save(out_path)  # Sauvegarde l'image convertie dans le dossier de sortie
        
        processing_time = time.perf_counter() - start_time  # Calcule le temps de traitement (temps actuel - temps de début)
        
        # ZONE CRITIQUE : Écriture dans le fichier log
        # Cette opération nécessite une synchronisation si plusieurs threads
        # ou processus y accèdent simultanément
        log_message = (  # Construit le message de log avec les informations de traitement
            f"Image traitée: {in_path.name} -> {out_path.name} "  # Nom de l'image source et destination
            f"(temps: {processing_time:.4f}s, thread: {thread_id or 'N/A'})"  # Temps de traitement et ID du thread
        )
        
        if _global_logger and use_lock:  # Si un logger global existe ET qu'on doit utiliser le lock
            # Utilise le logger thread-safe (avec lock)
            _global_logger.log(log_message)  # Écrit le message dans le log de manière thread-safe
        elif _global_logger:  # Si un logger global existe mais qu'on ne doit PAS utiliser le lock
            # Utilise le logger sans lock (pour démontrer les problèmes)
            # Note: Ceci peut causer des race conditions
            try:  # Bloc try pour gérer les erreurs d'écriture
                with open(_global_logger.log_file, 'a', encoding='utf-8') as f:  # Ouvre le fichier en mode append (ajout)
                    f.write(f"{log_message}\n")  # Écrit le message suivi d'un saut de ligne (SANS protection)
            except:  # Capture toutes les exceptions (erreurs d'écriture possibles)
                pass  # Ignore les erreurs (pour ne pas interrompre le traitement)
        
        return {  # Retourne un dictionnaire avec les informations de succès
            "success": True,  # Indique que la conversion a réussi
            "input": str(in_path),  # Chemin de l'image source (converti en string)
            "output": str(out_path),  # Chemin de l'image de sortie (converti en string)
            "processing_time": processing_time,  # Temps de traitement en secondes
            "thread_id": thread_id  # Identifiant du thread/processus
        }
    except Exception as e:  # Capture toutes les exceptions pendant le traitement
        error_time = time.perf_counter() - start_time  # Calcule le temps écoulé avant l'erreur
        error_msg = traceback.format_exc()  # Récupère la trace complète de l'erreur (formatée)
        
        # Log de l'erreur (zone critique)
        if _global_logger and use_lock:  # Si un logger global existe ET qu'on doit utiliser le lock
            _global_logger.log(f"ERREUR: {in_path.name} - {str(e)}")  # Écrit le message d'erreur dans le log de manière thread-safe
        
        return {  # Retourne un dictionnaire avec les informations d'erreur
            "success": False,  # Indique que la conversion a échoué
            "input": str(in_path),  # Chemin de l'image source (converti en string)
            "output": None,  # Pas d'image de sortie (échec)
            "error": error_msg,  # Message d'erreur complet avec traceback
            "processing_time": error_time,  # Temps écoulé avant l'erreur
            "thread_id": thread_id  # Identifiant du thread/processus
        }
