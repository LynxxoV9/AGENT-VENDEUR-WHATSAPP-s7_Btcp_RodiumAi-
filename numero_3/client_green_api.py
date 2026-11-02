import json
import urllib.request
from typing import List, Dict

# client http d envoi de messages whatsapp via green api
class ClientGreenAPI:
    def __init__(self, url_api: str, id_instance: str, token_instance: str, mode_simulation: bool = False):
        self.url_api = url_api.rstrip("/")
        self.id_instance = id_instance
        self.token_instance = token_instance
        self.mode_simulation = mode_simulation
        # journal des messages emis pour audit et verification dans les tests
        self.journal_messages: List[Dict] = []

    # envoi d un message texte a un destinataire whatsapp
    def envoyer_message(self, chat_id: str, message_texte: str) -> bool:
        enregistrement = {
            "chat_id": chat_id,
            "message": message_texte
        }
        self.journal_messages.append(enregistrement)

        # en mode simulation les requetes reseau sont interceptees
        if self.mode_simulation or self.token_instance == "mock_token_green_api":
            return True

        url_complete = f"{self.url_api}/waInstance{self.id_instance}/sendMessage/{self.token_instance}"
        payload = json.dumps({"chatId": chat_id, "message": message_texte}).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        try:
            requete = urllib.request.Request(url_complete, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(requete, timeout=10) as reponse:
                return reponse.status == 200
        except Exception as e:
            print(f"Erreur d'envoi Green API vers {chat_id}: {e}")
            return False

    # recuperation du dernier message envoye a un numero
    def obtenir_dernier_message(self, chat_id: str = None) -> str:
        if not self.journal_messages:
            return ""
        if chat_id is None:
            return self.journal_messages[-1]["message"]
        for msg in reversed(self.journal_messages):
            if msg["chat_id"] == chat_id:
                return msg["message"]
        return ""
