import sys
from pathlib import Path

# inclusion de la racine du projet et des sous-dossiers dans le PYTHONPATH
racine = Path(__file__).resolve().parent.parent
sys.path.append(str(racine))
sys.path.append(str(racine / "numero_1"))
sys.path.append(str(racine / "numero_2" / "fiabilite"))
sys.path.append(str(racine / "numero_3"))

from numero_3.serveur import app
