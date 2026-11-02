import re
from typing import Optional, Dict

# gestionnaire des commandes en attente de validation humaine sur whatsapp
class GestionnaireValidationWhatsApp:
    def __init__(self, numero_afi: str):
        self.numero_afi = numero_afi
        self.commandes_en_attente: Dict[int, dict] = {}
        self.compteur_commandes = 10

    # creation d une nouvelle demande de commande en attente
    def creer_demande_validation(self, chat_id_client: str, reference: str, produit: str, quantite: int, zone: str, total_fcfa: int) -> int:
        self.compteur_commandes += 1
        num_cmd = self.compteur_commandes
        self.commandes_en_attente[num_cmd] = {
            "id": num_cmd,
            "client_chat_id": chat_id_client,
            "reference": reference,
            "produit": produit,
            "quantite": quantite,
            "zone": zone,
            "total_fcfa": total_fcfa,
            "statut": "en_attente"
        }
        return num_cmd

    # generation du message whatsapp destine a afi
    def generer_message_afi(self, num_cmd: int) -> str:
        cmd = self.commandes_en_attente.get(num_cmd)
        if not cmd:
            return ""
        montant_formate = f"{cmd['total_fcfa']:,}".replace(",", " ")
        return (
            f"Commande #{cmd['id']} : {cmd['quantite']} {cmd['produit']}, "
            f"{cmd['zone']}, {montant_formate} FCFA. "
            f"Répondez OUI {cmd['id']} ou NON {cmd['id']}"
        )

    # analyse d un message pour detecter une decision de validation
    def analyser_decision_afi(self, expediteur_chat_id: str, texte_message: str) -> Optional[dict]:
        texte = texte_message.strip()
        match = re.search(r"^(OUI|NON)\s+(\d+)$", texte, re.IGNORECASE)
        if not match:
            return None

        decision = match.group(1).upper()
        num_cmd = int(match.group(2))

        # verification stricte de l identite de l expediteur
        if expediteur_chat_id != self.numero_afi:
            return {
                "autorise": False,
                "message_erreur": "Refusé : seul le numéro officiel d'Afi est autorisé à valider les commandes."
            }

        cmd = self.commandes_en_attente.get(num_cmd)
        if not cmd:
            return {
                "autorise": True,
                "valide": False,
                "message": f"Commande #{num_cmd} introuvable ou déjà traitée."
            }

        if decision == "OUI":
            cmd["statut"] = "validee"
            del self.commandes_en_attente[num_cmd]
            return {
                "autorise": True,
                "decision": "OUI",
                "commande": cmd
            }
        else:
            cmd["statut"] = "refusee"
            del self.commandes_en_attente[num_cmd]
            return {
                "autorise": True,
                "decision": "NON",
                "commande": cmd
            }
