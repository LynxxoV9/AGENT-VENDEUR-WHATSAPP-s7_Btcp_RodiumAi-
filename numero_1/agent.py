import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# import des outils et du registre
try:
    from outils import DEFINITIONS_OUTILS, REGISTRE_FONCTIONS
except ImportError:
    from numero_1.outils import DEFINITIONS_OUTILS, REGISTRE_FONCTIONS

# chargement des variables d environnement depuis le fichier env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("RODIUMAI_API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://api.rodiumai.io/v1")
MODELE = "google/gemini-3.8-flash"

# initialisation du client d appel compatible openai
client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

# definition du prompt systeme regissant le comportement du vendeur
SYSTEM_PROMPT = """Tu es l'agent vendeur WhatsApp de la boutique d'Afi, située au grand marché Dantokpa à Cotonou.
Ton rôle est de renseigner chaleureusement les clients, vérifier le stock, calculer les frais de livraison, convertir les prix et prendre les commandes.

Règles impératives de la boutique :
1. Aucun prix, stock ou frais ne doit être inventé : TOUT chiffre doit provenir obligatoirement d'un outil.
2. Si un produit est en rupture de stock, tu dois l'indiquer explicitement au client et proposer immédiatement une alternative proche disponible dans le catalogue.
3. Le total annoncé doit toujours être égal à la somme des articles + frais de livraison.
4. Une commande n'est validée et enregistrée qu'après accord explicite du client et confirmation de la boutique.
5. Les conversions de devises doivent obligatoirement utiliser l'outil convertir_devise avec le taux réel.
6. Pour toute question générale sur l'entretien des pagnes, les retours ou la boutique, utilise l'outil consulter_guide_boutique.
7. Sois concis et efficace : appelle uniquement les outils nécessaires pour répondre à la demande, sans multiplier les appels superflus.
8. Ton style doit être direct, poli, adapté à WhatsApp, avec des réponses concises (moins de 80 mots), prix toujours en FCFA avec conversion si demandée."""

# classe representant l agent vendeur avec sa boucle react
class AgentVendeur:
    def __init__(self, max_etapes: int = 10, max_historique: int = 12):
        self.max_etapes = max_etapes
        self.max_historique = max_historique
        self.historique = []

    # reinitialisation de l historique de conversation
    def reinitialiser(self):
        self.historique = []

    # execution d un tour conversationnel complet avec boucle react
    def executer(self, message_utilisateur: str, afficher_trace: bool = True) -> str:
        # ajout du message utilisateur dans l historique
        self.historique.append({"role": "user", "content": message_utilisateur})

        # limitation de l historique aux derniers messages pour preserver les tokens
        messages_actifs = [{"role": "system", "content": SYSTEM_PROMPT}]
        contexte_recent = self.historique[-self.max_historique:]
        messages_actifs.extend(contexte_recent)

        if afficher_trace:
            print(f"\n[CLIENT] : {message_utilisateur}")

        # boucle react penser agir observer evaluer
        etape = 0
        while etape < self.max_etapes:
            etape += 1

            # appel du modele avec basse temperature pour eviter les hallucinations
            reponse = client.chat.completions.create(
                model=MODELE,
                messages=messages_actifs,
                tools=DEFINITIONS_OUTILS,
                tool_choice="auto",
                temperature=0.1
            )

            message_assistant = reponse.choices[0].message
            tool_calls = message_assistant.tool_calls

            # verification si l agent a termine ou s il appelle des outils
            if not tool_calls:
                reponse_finale = message_assistant.content or ""
                self.historique.append({"role": "assistant", "content": reponse_finale})
                if afficher_trace:
                    print(f"[REPONSE FINALE] :\n{reponse_finale}")
                return reponse_finale

            # formatage propre sous forme de dictionnaire compatible api
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

            # execution des outils appeles
            for tool_call in tool_calls:
                nom_fonction = tool_call.function.name
                arguments_bruts = tool_call.function.arguments

                try:
                    arguments = json.loads(arguments_bruts)
                except Exception:
                    arguments = {}

                if afficher_trace:
                    print(f"  [ACTION] -> Appel outil: {nom_fonction} | Arguments: {arguments}")

                # execution de la fonction correspondante
                fonction = REGISTRE_FONCTIONS.get(nom_fonction)
                if fonction:
                    try:
                        observation = fonction(**arguments)
                    except Exception as e:
                        observation = f"erreur d execution de {nom_fonction}: {str(e)}"
                else:
                    observation = f"outil {nom_fonction} introuvable"

                if afficher_trace:
                    print(f"  [OBSERVATION] <- {observation}")

                # injection de l observation dans le contexte de la boucle
                messages_actifs.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": nom_fonction,
                    "content": str(observation)
                })

        # repli si le nombre d etapes maximal est atteint
        repli = "Désolé, je n'ai pas pu finaliser votre demande dans le temps imparti. Pouvez-vous préciser votre souhait ?"
        self.historique.append({"role": "assistant", "content": repli})
        return repli
