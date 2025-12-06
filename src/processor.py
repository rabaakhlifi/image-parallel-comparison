# src/processor.py
from PIL import Image, ImageOps
from pathlib import Path
import traceback

# Convertit une image en niveaux de gris et la sauvegarde dans le dossier de sortie
def convert_to_grayscale(input_path: str, output_dir: str, suffix="_gray") -> dict:
    """
    Convert an image to grayscale and save it to output_dir.
    Returns a dict with info (success, input, output, error).
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    in_path = Path(input_path)
    out_name = in_path.stem + suffix + in_path.suffix
    out_path = Path(output_dir) / out_name
    try:
        with Image.open(in_path) as img:
            # Convert to grayscale using Pillow
            gray = ImageOps.grayscale(img)
            gray.save(out_path)
        return {"success": True, "input": str(in_path), "output": str(out_path)}
    except Exception as e:
        return {"success": False, "input": str(in_path), "output": None, "error": traceback.format_exc()}
