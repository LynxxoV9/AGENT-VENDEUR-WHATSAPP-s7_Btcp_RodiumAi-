import json
from pathlib import Path

# determination des chemins des fichiers de persistance
DOSSIER_DONNEES = Path(__file__).resolve().parent.parent / "donnees"
FICHIER_STOCK = DOSSIER_DONNEES / "stock.json"
FICHIER_COMMANDES = DOSSIER_DONNEES / "commandes.json"

# chargement du stock persistant depuis le fichier json
def charger_stock() -> list:
    if not FICHIER_STOCK.exists():
        return []
    with open(FICHIER_STOCK, "r", encoding="utf-8") as f:
        return json.load(f)

# sauvegarde du stock dans le fichier json
def sauvegarder_stock(stock: list):
    with open(FICHIER_STOCK, "w", encoding="utf-8") as f:
        json.dump(stock, f, indent=2, ensure_ascii=False)

# chargement des commandes passees depuis le fichier json
def charger_commandes() -> list:
    if not FICHIER_COMMANDES.exists():
        return []
    with open(FICHIER_COMMANDES, "r", encoding="utf-8") as f:
        return json.load(f)

# enregistrement d une nouvelle commande dans le fichier persistant
def enregistrer_commande(commande: dict):
    commandes = charger_commandes()
    commandes.append(commande)
    with open(FICHIER_COMMANDES, "w", encoding="utf-8") as f:
        json.dump(commandes, f, indent=2, ensure_ascii=False)
