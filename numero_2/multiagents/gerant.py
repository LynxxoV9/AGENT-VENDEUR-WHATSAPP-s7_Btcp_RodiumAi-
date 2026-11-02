import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# imports des specialistes
from vendeur import traiter_demande_vendeur
from logisticien import traiter_demande_logisticien
from redacteur import rediger_reponse_whatsapp

# inclusion du dossier fiabilite pour l evaluation
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent / "fiabilite"))
from evaluateur import evaluer_reponse_complete

# chargement des variables d environnement
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

client = OpenAI(
    api_key=os.getenv("RODIUMAI_API_KEY"),
    base_url=os.getenv("BASE_URL", "https://api.rodiumai.io/v1")
)
MODELE = "google/gemini-3.8-flash"

# definitions des outils delegatifs pour le gerant
OUTILS_GERANT = [
    {
        "type": "function",
        "function": {
            "name": "demander_au_vendeur",
            "description": "Consulte le Vendeur pour les questions de produits, prix unitaires, stocks et commandes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "La question commerciale précise à poser au vendeur."}
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "demander_au_logisticien",
            "description": "Consulte le Logisticien pour les zones, frais de livraison et conversions de devises.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "La question logistique précise à poser."}
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "demander_au_redacteur",
            "description": "Transmet au Rédacteur l'ensemble des données vérifiées pour rédiger le message WhatsApp final.",
            "parameters": {
                "type": "object",
                "properties": {
                    "donnees_a_formater": {"type": "string", "description": "Toutes les informations vérifiées à mettre en forme."}
                },
                "required": ["donnees_a_formater"]
            }
        }
    }
]

PROMPT_GERANT = """Tu es le Gérant et chef d'orchestre de la boutique d'Afi à Dantokpa.
Tu ne traites pas directement avec les outils de bas niveau, mais tu coordonnes ton équipe de spécialistes :
1. Tu demandes au Vendeur pour tout ce qui touche aux articles, prix et stocks (demander_au_vendeur).
2. Tu demandes au Logisticien pour les frais de livraison et conversions de monnaies (demander_au_logisticien).
3. Une fois les données récoltées, tu confies la mise en forme au Rédacteur (demander_au_redacteur).

Règles de gestion :
- Aucun chiffre ne doit être inventé : tout doit provenir des résumés de tes spécialistes.
- Le total annoncé doit obligatoirement être égal à la somme des articles + livraison."""

# classe representant l architecture multi agents orchestree par le gerant
class EquipeBoutique:
    def __init__(self, max_etapes: int = 10):
        self.max_etapes = max_etapes
        self.historique = []

    # reinitialisation de l historique du gerant
    def reinitialiser(self):
        self.historique = []

    # execution de l orchestration multi agents
    def executer(self, message_client: str, afficher_trace: bool = True) -> str:
        self.historique.append({"role": "user", "content": message_client})

        messages_actifs = [
            {"role": "system", "content": PROMPT_GERANT},
            {"role": "user", "content": message_client}
        ]

        if afficher_trace:
            print(f"\n[CLIENT] : {message_client}")

        observations_gerant = []
        etape = 0

        while etape < self.max_etapes:
            etape += 1

            reponse = client.chat.completions.create(
                model=MODELE,
                messages=messages_actifs,
                tools=OUTILS_GERANT,
                tool_choice="auto",
                temperature=0.1
            )

            msg = reponse.choices[0].message
            tool_calls = msg.tool_calls

            # reponse finale sans delegation
            if not tool_calls:
                reponse_finale = msg.content or ""
                # evaluation de la reponse finale au niveau du gerant
                valide, critique = evaluer_reponse_complete(
                    client=client,
                    modele=MODELE,
                    message_client=message_client,
                    reponse_texte=reponse_finale,
                    observations_outils=observations_gerant
                )
                if not valide:
                    if afficher_trace:
                        print(f"  [GERANT EVALUATION] <- Rejetée : {critique}")
                    messages_actifs.append({"role": "assistant", "content": reponse_finale})
                    messages_actifs.append({
                        "role": "user",
                        "content": f"Critique d'évaluation : {critique}. Corrige la réponse avec le rédacteur."
                    })
                    continue

                if afficher_trace:
                    print(f"[REPONSE FINALE GERANT] :\n{reponse_finale}")
                return reponse_finale

            # enregistrement de l appel de delegation
            messages_actifs.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                    }
                    for tc in tool_calls
                ]
            })

            # execution des delegations
            for tc in tool_calls:
                nom = tc.function.name
                args = json.loads(tc.function.arguments)

                if afficher_trace:
                    print(f"  [DELEGATION] -> {nom} avec {args}")

                if nom == "demander_au_vendeur":
                    observation = traiter_demande_vendeur(args.get("question", ""))
                elif nom == "demander_au_logisticien":
                    observation = traiter_demande_logisticien(args.get("question", ""))
                elif nom == "demander_au_redacteur":
                    donnees = args.get("donnees_a_formater", "")
                    observation = rediger_reponse_whatsapp(donnees, message_client)
                else:
                    observation = f"spécialiste inconnu {nom}"

                if afficher_trace:
                    print(f"  [RETOUR SPECIALISTE] <- {observation}")

                observations_gerant.append(str(observation))

                messages_actifs.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": nom,
                    "content": str(observation)
                })

        return "Désolé, la coordination a pris trop d'étapes."
