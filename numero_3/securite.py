import time
import re

# gestionnaire du dedoublonnage des messages entrants
class GestionnaireDedoublonnage:
    def __init__(self, duree_conservation_secondes: int = 3600):
        self.duree = duree_conservation_secondes
        self.messages_vus = {}

    # verification et enregistrement de l identifiant de message
    def est_deja_traite(self, id_message: str) -> bool:
        maintenant = time.time()
        # nettoyage des identifiants expires
        expires = [msg_id for msg_id, ts in self.messages_vus.items() if maintenant - ts > self.duree]
        for exp in expires:
            del self.messages_vus[exp]

        if id_message in self.messages_vus:
            return True

        self.messages_vus[id_message] = maintenant
        return False

# limiteur de debit pour respecter le budget de requetes par client
class LimiteurDebit:
    def __init__(self, max_par_heure: int = 30):
        self.max_par_heure = max_par_heure
        self.requetes_clients = {}

    # verification si un client a depasse son quota horaire
    def autoriser_requete(self, chat_id: str) -> bool:
        maintenant = time.time()
        if chat_id not in self.requetes_clients:
            self.requetes_clients[chat_id] = []

        # filtrage des requetes de la derniere heure
        historique = [ts for ts in self.requetes_clients[chat_id] if maintenant - ts < 3600]
        self.requetes_clients[chat_id] = historique

        if len(historique) >= self.max_par_heure:
            return False

        self.requetes_clients[chat_id].append(maintenant)
        return True

# filtre de securite contre les tentatives d injection de prompt
class FiltreInjection:
    MOTS_SUSPECTS = [
        r"ignore\s+(?:toutes?\s+)?(?:tes|les)\s+instructions",
        r"oublie\s+(?:toutes?\s+)?(?:tes|les)\s+règles",
        r"mets\s+tout\s+à\s+0",
        r"le\s+prix\s+est\s+(?:de\s+)?0",
        r"je\s+suis\s+l'administrateur",
        r"mode\s+developpeur"
    ]

    # detection de motifs d injection dans le texte
    @classmethod
    def contient_injection(cls, texte: str) -> bool:
        texte_min = texte.lower()
        for motif in cls.MOTS_SUSPECTS:
            if re.search(motif, texte_min):
                return True
        return False
