import json
import urllib.request
import re
from pathlib import Path

# import du gestionnaire persistant
from gestionnaire_stock import charger_stock, sauvegarder_stock, enregistrer_commande

# import des zones de livraison
try:
    from catalogue import ZONES_LIVRAISON
except ImportError:
    from numero_1.catalogue import ZONES_LIVRAISON

# variable globale pour la fonction de validation humaine configurable
HOOK_VALIDATION_HUMAINE = None

# configuration du hook de validation pour les tests automatises
def configurer_hook_validation(hook):
    global HOOK_VALIDATION_HUMAINE
    HOOK_VALIDATION_HUMAINE = hook

# recherche de produits dans le stock persistant
def chercher_produits(mot_cle: str) -> str:
    stock = charger_stock()
    terme = mot_cle.lower().strip()
    resultats = []
    for item in stock:
        nom = item["produit"].lower()
        categorie = item["categorie"].lower()
        ref = item["reference"].lower()
        if not terme or terme in nom or terme in categorie or terme in ref:
            resultats.append(item)
    if not resultats:
        return f"aucun produit pour {mot_cle}"
    lignes = []
    for p in resultats:
        statut = f"en stock ({p['stock']})" if p["stock"] > 0 else "rupture de stock"
        lignes.append(f"- Ref: {p['reference']} | {p['produit']} | Prix: {p['prix_fcfa']} FCFA | {statut}")
    return "\n".join(lignes)

# verification du stock persistant pour une reference
def verifier_stock(reference: str) -> str:
    stock = charger_stock()
    ref_norm = reference.strip().upper()
    for item in stock:
        if item["reference"].upper() == ref_norm:
            return f"Produit: {item['produit']} (Ref: {item['reference']}) | Stock disponible: {item['stock']} | Prix: {item['prix_fcfa']} FCFA"
    return "référence inconnue"

# calcul des frais et delais de livraison selon la zone
def frais_livraison(zone: str) -> str:
    zone_cle = zone.strip().lower()
    cle_normalisee = re.sub(r"[^a-z0-9]", "", zone_cle)
    for cle, info in ZONES_LIVRAISON.items():
        if cle_normalisee == re.sub(r"[^a-z0-9]", "", cle):
            return f"Zone: {info['nom']} | Frais: {info['frais_fcfa']} FCFA | Délai: {info['delai']}"
    zones_valides = ", ".join([info["nom"] for info in ZONES_LIVRAISON.values()])
    return f"zone non desservie. Zones desservies: {zones_valides}"

# conversion d un montant fcfa vers une devise cible
def convertir_devise(montant_fcfa: float, devise_cible: str) -> str:
    devise = devise_cible.strip().upper()
    url = "https://open.er-api.com/v6/latest/XOF"
    taux = None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BoutiqueAfiAgent/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data.get("result") == "success" and "rates" in data:
                taux = data["rates"].get(devise)
    except Exception:
        parites_repli = {
            "EUR": 0.001524,
            "USD": 0.001650,
            "NGN": 2.450000,
            "GBP": 0.001300,
            "CAD": 0.002250
        }
        taux = parites_repli.get(devise)

    if taux is None:
        return "devise non prise en charge"

    montant_converti = round(montant_fcfa * taux, 2)
    return f"{montant_fcfa} FCFA = {montant_converti} {devise} (taux: {taux})"

# enregistrement d une commande avec validation humaine et memoire persistante
def creer_commande(reference: str, quantite: int, zone: str) -> str:
    stock = charger_stock()
    ref_norm = reference.strip().upper()
    produit_trouve = None
    for item in stock:
        if item["reference"].upper() == ref_norm:
            produit_trouve = item
            break

    if not produit_trouve:
        return "référence inconnue"

    if produit_trouve["stock"] < quantite:
        return f"stock insuffisant pour {produit_trouve['produit']}"

    # etape obligatoire de validation humaine avant enregistrement
    global HOOK_VALIDATION_HUMAINE
    if HOOK_VALIDATION_HUMAINE is not None:
        accord = HOOK_VALIDATION_HUMAINE(produit_trouve, quantite, zone)
    else:
        reponse_humaine = input(f"Valider la commande pour {quantite}x {produit_trouve['produit']} à {zone} ? [o/N] : ").strip().lower()
        accord = reponse_humaine in ["o", "oui", "y", "yes"]

    # traitement du refus humain renvoye a l agent comme une observation
    if not accord:
        return "refus de validation par Afi : commande non enregistrée"

    # decrementation du stock persistant en cas d accord
    produit_trouve["stock"] -= quantite
    sauvegarder_stock(stock)

    # persistance de la commande confirmee
    nouvelle_commande = {
        "reference": ref_norm,
        "produit": produit_trouve["produit"],
        "quantite": quantite,
        "prix_unitaire_fcfa": produit_trouve["prix_fcfa"],
        "total_articles_fcfa": produit_trouve["prix_fcfa"] * quantite,
        "zone": zone,
        "statut": "validee"
    }
    enregistrer_commande(nouvelle_commande)

    return f"Commande validée et enregistrée: {quantite}x {produit_trouve['produit']} pour la zone {zone}. Nouveau stock: {produit_trouve['stock']}"

# consultation du guide officiel via rag
def consulter_guide_boutique(sujet: str) -> str:
    chemin_guide = Path(__file__).resolve().parent.parent.parent / "articles" / "guide_boutique.md"
    if not chemin_guide.exists():
        return "Guide de la boutique indisponible"
    contenu = chemin_guide.read_text(encoding="utf-8")
    sections = contenu.split("\n## ")
    termes = sujet.lower().split()
    meilleures_sections = []
    for sec in sections:
        sec_texte = sec.lower()
        score = sum(1 for t in termes if t in sec_texte)
        if score > 0:
            meilleures_sections.append((score, sec))
    if not meilleures_sections:
        return sections[0] if sections else "Information non trouvée dans le guide"
    meilleures_sections.sort(key=lambda x: x[0], reverse=True)
    extraits = [s[1] for s in meilleures_sections[:2]]
    return "\n## ".join(extraits)

# definitions json schema des outils fiables
DEFINITIONS_OUTILS_FIABLES = [
    {
        "type": "function",
        "function": {
            "name": "chercher_produits",
            "description": "Trouve des produits par mot-clé dans le stock persistant de la boutique Dantokpa.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mot_cle": {"type": "string", "description": "Mot-clé pour la recherche (ex: wax, robe, sac)."}
                },
                "required": ["mot_cle"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "verifier_stock",
            "description": "Donne le stock persistant et les détails d'un produit par référence (ex: P01, P05).",
            "parameters": {
                "type": "object",
                "properties": {
                    "reference": {"type": "string", "description": "Référence unique du produit."}
                },
                "required": ["reference"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "frais_livraison",
            "description": "Donne les frais et le délai de livraison pour une zone géographique.",
            "parameters": {
                "type": "object",
                "properties": {
                    "zone": {"type": "string", "description": "Nom de la ville ou du quartier de livraison."}
                },
                "required": ["zone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "convertir_devise",
            "description": "Convertit un montant FCFA vers une autre devise via un taux de change réel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "montant_fcfa": {"type": "number", "description": "Montant en FCFA à convertir."},
                    "devise_cible": {"type": "string", "description": "Code ISO de la devise cible (EUR, NGN, USD)."}
                },
                "required": ["montant_fcfa", "devise_cible"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "creer_commande",
            "description": "Enregistre une commande avec validation humaine préalable d'Afi.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reference": {"type": "string", "description": "Référence du produit commandé."},
                    "quantite": {"type": "integer", "description": "Quantité commandée."},
                    "zone": {"type": "string", "description": "Zone de livraison."}
                },
                "required": ["reference", "quantite", "zone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consulter_guide_boutique",
            "description": "Consulte le guide officiel de la boutique via RAG.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sujet": {"type": "string", "description": "Sujet recherché."}
                },
                "required": ["sujet"]
            }
        }
    }
]

# registre des fonctions fiables
REGISTRE_FONCTIONS_FIABLES = {
    "chercher_produits": chercher_produits,
    "verifier_stock": verifier_stock,
    "frais_livraison": frais_livraison,
    "convertir_devise": convertir_devise,
    "creer_commande": creer_commande,
    "consulter_guide_boutique": consulter_guide_boutique
}
