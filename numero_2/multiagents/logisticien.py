import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# inclusion du dossier fiabilite pour acceder aux outils de livraison
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent / "fiabilite"))
from outils_fiables import frais_livraison, convertir_devise

# chargement des variables d environnement
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

client = OpenAI(
    api_key=os.getenv("RODIUMAI_API_KEY"),
    base_url=os.getenv("BASE_URL", "https://api.rodiumai.io/v1")
)
MODELE = "google/gemini-3.8-flash"

# definitions des outils alloues au logisticien
OUTILS_LOGISTICIEN = [
    {
        "type": "function",
        "function": {
            "name": "frais_livraison",
            "description": "Donne les frais et délais pour une zone géographique.",
            "parameters": {
                "type": "object",
                "properties": {"zone": {"type": "string"}},
                "required": ["zone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "convertir_devise",
            "description": "Convertit un montant FCFA vers une autre devise au taux réel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "montant_fcfa": {"type": "number"},
                    "devise_cible": {"type": "string"}
                },
                "required": ["montant_fcfa", "devise_cible"]
            }
        }
    }
]

REGISTRE_LOGISTICIEN = {
    "frais_livraison": frais_livraison,
    "convertir_devise": convertir_devise
}

PROMPT_LOGISTICIEN = """Tu es le Logisticien spécialiste de la boutique d'Afi.
Ton rôle est de donner les frais de livraison exacts selon la zone et de convertir les montants en devises étrangères via tes outils.
Tout chiffre doit provenir de tes outils."""

# execution d une requete adressee au logisticien par le gerant
def traiter_demande_logisticien(instruction: str) -> str:
    messages = [
        {"role": "system", "content": PROMPT_LOGISTICIEN},
        {"role": "user", "content": instruction}
    ]

    for _ in range(5):
        reponse = client.chat.completions.create(
            model=MODELE,
            messages=messages,
            tools=OUTILS_LOGISTICIEN,
            tool_choice="auto",
            temperature=0.1
        )
        msg = reponse.choices[0].message
        if not msg.tool_calls:
            return msg.content or ""

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
            fn = REGISTRE_LOGISTICIEN.get(nom)
            obs = fn(**args) if fn else f"outil inconnu {nom}"
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "name": nom,
                "content": str(obs)
            })

    return "Information logistique indisponible"
