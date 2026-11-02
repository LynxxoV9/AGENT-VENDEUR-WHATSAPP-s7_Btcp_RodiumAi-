import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# imports relatifs des modules de fiabilite
from outils_fiables import DEFINITIONS_OUTILS_FIABLES, REGISTRE_FONCTIONS_FIABLES
from evaluateur import evaluer_reponse_complete

# chargement des variables d environnement
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("RODIUMAI_API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://api.rodiumai.io/v1")
MODELE = "google/gemini-3.8-flash"

# initialisation du client compatible openai
client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

# definition du prompt systeme renforce pour l agent fiable
SYSTEM_PROMPT_FIABLE = """Tu es l'agent vendeur de la boutique d'Afi au marché Dantokpa à Cotonou.
Tu réponds aux clients sur WhatsApp avec courtoisie, exactitude et concision.

Règles impératives de la boutique :
1. Aucun prix, stock ou frais ne doit être inventé : TOUT chiffre doit provenir obligatoirement d'un outil.
2. Si un produit est en rupture de stock, tu dois l'indiquer explicitement et proposer une alternative concrète du catalogue.
3. Le total annoncé doit toujours être égal à la somme exacte des articles commandés + frais de livraison.
4. Une commande nécessite la confirmation explicite du client avant d'appeler creer_commande.
5. Si un outil signale un refus de validation par Afi, tu dois en informer poliment le client.
6. Ta réponse doit impérativement faire moins de 80 mots et adopter un ton WhatsApp professionnel."""

# classe representant l agent vendeur fiable avec auto evaluation
class AgentVendeurFiable:
    def __init__(self, max_etapes: int = 10, max_historique: int = 12):
        self.max_etapes = max_etapes
        self.max_historique = max_historique
        self.historique = []

    # reinitialisation de l historique
    def reinitialiser(self):
        self.historique = []

    # execution d un tour conversationnel avec boucle react et evaluation
    def executer(self, message_utilisateur: str, afficher_trace: bool = True) -> str:
        self.historique.append({"role": "user", "content": message_utilisateur})

        messages_actifs = [{"role": "system", "content": SYSTEM_PROMPT_FIABLE}]
        contexte_recent = self.historique[-self.max_historique:]
        messages_actifs.extend(contexte_recent)

        observations_tour = []

        if afficher_trace:
            print(f"\n[CLIENT] : {message_utilisateur}")

        etape = 0
        while etape < self.max_etapes:
            etape += 1

            reponse = client.chat.completions.create(
                model=MODELE,
                messages=messages_actifs,
                tools=DEFINITIONS_OUTILS_FIABLES,
                tool_choice="auto",
                temperature=0.1
            )

            message_assistant = reponse.choices[0].message
            tool_calls = message_assistant.tool_calls

            # si aucune action n est demandee on evalue la reponse avant de la valider
            if not tool_calls:
                reponse_candidat = message_assistant.content or ""

                if afficher_trace:
                    print(f"  [EVALUATION] -> Vérification de la réponse candidate...")

                valide, critique = evaluer_reponse_complete(
                    client=client,
                    modele=MODELE,
                    message_client=message_utilisateur,
                    reponse_texte=reponse_candidat,
                    observations_outils=observations_tour
                )

                if valide:
                    if afficher_trace:
                        print(f"  [EVALUATION] <- Validée avec succès.")
                        print(f"[REPONSE FINALE] :\n{reponse_candidat}")
                    self.historique.append({"role": "assistant", "content": reponse_candidat})
                    return reponse_candidat
                else:
                    if afficher_trace:
                        print(f"  [EVALUATION] <- Rejetée ('pas encore') : {critique}")
                    # ajout de la critique dans le contexte pour auto correction
                    messages_actifs.append({"role": "assistant", "content": reponse_candidat})
                    messages_actifs.append({
                        "role": "user",
                        "content": f"ÉVALUATION CRITIQUE : {critique}. Corrige ta réponse immédiatement en respectant tous les critères."
                    })
                    continue

            # formatage conforme pour l historique de message assistant
            assistant_dict = {
                "role": "assistant",
                "content": message_assistant.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in tool_calls
                ]
            }
            messages_actifs.append(assistant_dict)

            # execution des outils selectionnes
            for tool_call in tool_calls:
                nom_fonction = tool_call.function.name
                arguments_bruts = tool_call.function.arguments

                try:
                    arguments = json.loads(arguments_bruts)
                except Exception:
                    arguments = {}

                if afficher_trace:
                    print(f"  [ACTION] -> Appel outil: {nom_fonction} | Arguments: {arguments}")

                fonction = REGISTRE_FONCTIONS_FIABLES.get(nom_fonction)
                if fonction:
                    try:
                        observation = fonction(**arguments)
                    except Exception as e:
                        observation = f"erreur d execution de {nom_fonction}: {str(e)}"
                else:
                    observation = f"outil {nom_fonction} introuvable"

                if afficher_trace:
                    print(f"  [OBSERVATION] <- {observation}")

                observations_tour.append(str(observation))

                messages_actifs.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": nom_fonction,
                    "content": str(observation)
                })

        repli = "Désolé, impossible de finaliser le traitement après plusieurs vérifications."
        self.historique.append({"role": "assistant", "content": repli})
        return repli
