import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# chargement des variables d environnement
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

client = OpenAI(
    api_key=os.getenv("RODIUMAI_API_KEY"),
    base_url=os.getenv("BASE_URL", "https://api.rodiumai.io/v1")
)
MODELE = "google/gemini-3.8-flash"

PROMPT_REDACTEUR = """Tu es le Rédacteur WhatsApp de la boutique d'Afi au marché Dantokpa.
Tu ne disposes d'aucun outil. Ton seul et unique rôle est de formater les informations brutes fournies par l'équipe en un message WhatsApp élégant, chaleureux et percutant.

Règles impératives :
1. N'ajoute, ne déduis et n'invente AUCUN chiffre ni prix qui ne figure pas dans les données fournies.
2. Utilise le ton convivial et direct du commerce ouest-africain sur WhatsApp.
3. Ta réponse finale doit compter strictement moins de 80 mots."""

# redaction finale du message whatsapp a partir des donnees transmises par le gerant
def rediger_reponse_whatsapp(donnees_brutes: str, demande_initiale: str) -> str:
    messages = [
        {"role": "system", "content": PROMPT_REDACTEUR},
        {
            "role": "user",
            "content": f"Demande du client : {demande_initiale}\nDonnées vérifiées par l'équipe : {donnees_brutes}\nFormate la réponse finale :"
        }
    ]

    reponse = client.chat.completions.create(
        model=MODELE,
        messages=messages,
        temperature=0.2
    )

    return reponse.choices[0].message.content or ""
