import sys, os

# Ajouter le dossier parent (/app) au PYTHONPATH
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(BASE_DIR)

from database import init_db

print("Initialisation de la base Railway…")
init_db()
print("✔ Base initialisée avec succès !")
