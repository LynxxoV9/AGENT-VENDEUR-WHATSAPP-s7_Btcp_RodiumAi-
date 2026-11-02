import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# inclusion du dossier fiabilite pour acceder aux outils de stock
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent / "fiabilite"))
from outils_fiables import chercher_produits, verifier_stock, creer_commande

# chargement des variables d environnement
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

client = OpenAI(
    api_key=os.getenv("RODIUMAI_API_KEY"),
    base_url=os.getenv("BASE_URL", "https://api.rodiumai.io/v1")
)
MODELE = "google/gemini-3.8-flash"

# definitions des outils alloues au vendeur
OUTILS_VENDEUR = [
    {
        "type": "function",
        "function": {
            "name": "chercher_produits",
            "description": "Trouve des articles par mot-clé dans le stock.",
            "parameters": {
                "type": "object",
                "properties": {"mot_cle": {"type": "string"}},
                "required": ["mot_cle"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "verifier_stock",
            "description": "Vérifie le stock et le prix d'un produit par référence.",
            "parameters": {
                "type": "object",
                "properties": {"reference": {"type": "string"}},
                "required": ["reference"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "creer_commande",
            "description": "Enregistre une commande après validation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reference": {"type": "string"},
                    "quantite": {"type": "integer"},
                    "zone": {"type": "string"}
                },
                "required": ["reference", "quantite", "zone"]
            }
        }
    }
]

REGISTRE_VENDEUR = {
    "chercher_produits": chercher_produits,
    "verifier_stock": verifier_stock,
    "creer_commande": creer_commande
}

PROMPT_VENDEUR = """Tu es le Vendeur spécialiste de la boutique d'Afi à Dantokpa.
Ton rôle est de répondre avec exactitude aux questions sur les produits, les prix unitaires, les stocks disponibles, et d'enregistrer les commandes.
Tout chiffre doit provenir de tes outils."""

# execution d une requete adressee au vendeur par le gerant
def traiter_demande_vendeur(instruction: str) -> str:
    messages = [
        {"role": "system", "content": PROMPT_VENDEUR},
        {"role": "user", "content": instruction}
    ]

    for _ in range(5):
        reponse = client.chat.completions.create(
            model=MODELE,
            messages=messages,
            tools=OUTILS_VENDEUR,
            tool_choice="auto",
            temperature=0.1
        )
        msg = reponse.choices[0].message
        if not msg.tool_calls:
            return msg.content or ""

        # ajout du message assistant
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                }
                for tc in msg.tool_calls
            ]
        })

        for tc in msg.tool_calls:
            nom = tc.function.name
            args = json.loads(tc.function.arguments)
            fn = REGISTRE_VENDEUR.get(nom)
            obs = fn(**args) if fn else f"outil inconnu {nom}"
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": nom,
                "content": str(obs)
            })

    return "Information vendeur indisponible"
