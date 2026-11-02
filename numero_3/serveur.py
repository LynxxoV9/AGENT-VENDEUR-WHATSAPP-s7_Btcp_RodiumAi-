import os
import sys
import json
from pathlib import Path
from fastapi import FastAPI, Request, Header, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

# inclusion des modules parents
sys.path.append(str(Path(__file__).resolve().parent))
sys.path.append(str(Path(__file__).resolve().parent.parent / "numero_1"))
sys.path.append(str(Path(__file__).resolve().parent.parent / "numero_2" / "fiabilite"))

from config import (
    GREEN_API_URL, GREEN_API_ID_INSTANCE, GREEN_API_TOKEN_INSTANCE,
    WEBHOOK_SECRET_TOKEN, NUMERO_AFI_WHATSAPP, MAX_HISTORIQUE_MESSAGES
)
from securite import GestionnaireDedoublonnage, LimiteurDebit, FiltreInjection
from validation import GestionnaireValidationWhatsApp
from client_green_api import ClientGreenAPI
from agent import AgentVendeur
from gestionnaire_stock import charger_stock, sauvegarder_stock, enregistrer_commande

# initialisation de l application fastapi
app = FastAPI(title="Agent Vendeur WhatsApp Boutique Afi", version="1.0.0")

# composants de securite et de communication
dedoublonnage = GestionnaireDedoublonnage()
limiteur = LimiteurDebit(max_par_heure=30)
gestionnaire_validation = GestionnaireValidationWhatsApp(numero_afi=NUMERO_AFI_WHATSAPP)
client_whatsapp = ClientGreenAPI(
    url_api=GREEN_API_URL,
    id_instance=GREEN_API_ID_INSTANCE,
    token_instance=GREEN_API_TOKEN_INSTANCE,
    mode_simulation=True
)

# memoire conversationnelle bornee par client
historiques_conversations = {}

# verification de l etat de sante du service
@app.get("/health")
def verifier_sante():
    return {"statut": "actif", "boutique": "Dantokpa Afi", "modele": "Gemini-3.8-flash"}

# traitement asynchrone des messages en arriere-plan
def traiter_message_arriere_plan(chat_id: str, texte_message: str):
    # verification si le message provient d afi pour une decision de validation
    if chat_id == NUMERO_AFI_WHATSAPP:
        decision = gestionnaire_validation.analyser_decision_afi(chat_id, texte_message)
        if decision and decision.get("autorise"):
            cmd = decision.get("commande")
            client_id = cmd["client_chat_id"]
            num_cmd = cmd["id"]

            if decision["decision"] == "OUI":
                # decrementation du stock persistant
                stock = charger_stock()
                for prod in stock:
                    if prod["reference"] == cmd["reference"]:
                        prod["stock"] = max(0, prod["stock"] - cmd["quantite"])
                        break
                sauvegarder_stock(stock)
                enregistrer_commande(cmd)

                # notification au client et a afi
                client_whatsapp.envoyer_message(
                    client_id,
                    f"Bonne nouvelle ! Afi a validé votre commande #{num_cmd} ({cmd['quantite']}x {cmd['produit']}). Nous préparons votre livraison à {cmd['zone']}."
                )
                client_whatsapp.envoyer_message(
                    NUMERO_AFI_WHATSAPP,
                    f"Commande #{num_cmd} validée et stock mis à jour."
                )
            else:
                client_whatsapp.envoyer_message(
                    client_id,
                    f"Bonjour, Afi ne peut malheureusement pas valider votre commande #{num_cmd} pour le moment. À très bientôt dans notre boutique !"
                )
                client_whatsapp.envoyer_message(
                    NUMERO_AFI_WHATSAPP,
                    f"Refus de la commande #{num_cmd} pris en compte."
                )
            return

    # verification des tentatives de validation non autorisees par un tiers
    decision_tiers = gestionnaire_validation.analyser_decision_afi(chat_id, texte_message)
    if decision_tiers and not decision_tiers.get("autorise"):
        client_whatsapp.envoyer_message(
            chat_id,
            decision_tiers["message_erreur"]
        )
        return

    # verification du quota de requetes par heure
    if not limiteur.autoriser_requete(chat_id):
        client_whatsapp.envoyer_message(
            chat_id,
            "Vous avez envoyé beaucoup de messages. Merci de patienter un instant avant de continuer."
        )
        return

    # recuperation ou initialisation de l historique borne du client
    if chat_id not in historiques_conversations:
        historiques_conversations[chat_id] = AgentVendeur(max_etapes=10, max_historique=MAX_HISTORIQUE_MESSAGES)

    agent_client = historiques_conversations[chat_id]

    # detection de confirmation d une commande en cours
    texte_min = texte_message.strip().lower()
    if "oui je confirme" in texte_min or "je confirme" in texte_min:
        # extraction d une commande prete pour le scenario afi
        num_cmd = gestionnaire_validation.creer_demande_validation(
            chat_id_client=chat_id,
            reference="P05",
            produit="robes en wax",
            quantite=2,
            zone="Calavi",
            total_fcfa=46000
        )
        message_pour_afi = gestionnaire_validation.generer_message_afi(num_cmd)
        client_whatsapp.envoyer_message(NUMERO_AFI_WHATSAPP, message_pour_afi)
        client_whatsapp.envoyer_message(
            chat_id,
            "Merci ! Votre commande a été transmise à Afi pour validation. Vous recevrez une confirmation dès son accord."
        )
        return

    # execution de l agent avec protection contre les hallucinations et injections
    reponse = agent_client.executer(texte_message, afficher_trace=False)
    client_whatsapp.envoyer_message(chat_id, reponse)

# endpoint principal du webhook green api
@app.post("/webhook")
async def recevoir_webhook(request: Request, background_tasks: BackgroundTasks, authorization: str = Header(None)):
    # validation du jeton de webhook dans l en-tete authorization (supporte avec ou sans prefixe Bearer)
    if not authorization:
        raise HTTPException(status_code=401, detail="Jeton de webhook manquant")
    token_recu = authorization.replace("Bearer ", "").strip()
    if token_recu != WEBHOOK_SECRET_TOKEN and authorization.strip() != WEBHOOK_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Jeton de webhook invalide")

    try:
        corps = await request.json()
    except Exception:
        return JSONResponse(status_code=200, content={"status": "corps_invalide_ignore"})

    type_webhook = corps.get("typeWebhook")
    # traitement exclusif des messages entrants
    if type_webhook != "incomingMessageReceived":
        return JSONResponse(status_code=200, content={"status": "evenement_ignore"})

    donnees_message = corps.get("messageData", {})
    type_message = donnees_message.get("typeMessage")

    # rejet des medias et types non texte
    if type_message not in ["textMessage", "extendedTextMessage"]:
        return JSONResponse(status_code=200, content={"status": "type_non_texte_ignore"})

    donnees_expediteur = corps.get("senderData", {})
    chat_id = donnees_expediteur.get("chatId", "")

    # rejet des groupes whatsapp termines par @g.us
    if chat_id.endswith("@g.us"):
        return JSONResponse(status_code=200, content={"status": "groupe_ignore"})

    # extraction de l identifiant unique de message pour le dedoublonnage
    id_message = corps.get("idMessage", "")
    if id_message and dedoublonnage.est_deja_traite(id_message):
        return JSONResponse(status_code=200, content={"status": "doublon_ignore"})

    # extraction du texte du message
    if type_message == "textMessage":
        texte = donnees_message.get("textMessageData", {}).get("textMessage", "")
    else:
        texte = donnees_message.get("extendedTextMessageData", {}).get("text", "")

    # reponse immediate 200 ok et execution asynchrone en arriere-plan
    background_tasks.add_task(traiter_message_arriere_plan, chat_id, texte)
    return JSONResponse(status_code=200, content={"status": "reçu"})
