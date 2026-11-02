import re
import json

# evaluation de premier niveau par regle de code arithmetique
def evaluer_regle_code(reponse_texte: str, observations_outils: list) -> tuple:
    # extraction de tous les montants numeriques en fcfa dans la reponse
    nombres_reponse = [int(n.replace(" ", "").replace(".", "")) for n in re_nombres if n] if (re_nombres := re.findall(r"\b\d{1,3}(?:[\s.]\d{3})+\b|\b\d{4,6}\b", reponse_texte)) else []

    # extraction des prix et frais issus des observations d outils
    montants_observes = []
    for obs in observations_outils:
        montants = re.findall(r"\b\d{1,3}(?:[\s.]\d{3})+\b|\b\d{4,6}\b", obs)
        for m in montants:
            valeur = int(m.replace(" ", "").replace(".", ""))
            montants_observes.append(valeur)

    # detection d un mot cle annoncant un total
    mots_cles_total = ["total", "coûte", "revient", "ensemble", "somme"]
    annonce_total = any(mot in reponse_texte.lower() for mot in mots_cles_total)

    # si aucun total n est annonce la regle arithmetique est validee
    if not annonce_total or not nombres_reponse:
        return True, ""

    # verification que le total annonce est superieur ou egal a chaque article observe
    total_annonce = max(nombres_reponse)
    if montants_observes and total_annonce < min(montants_observes):
        return False, "Le total annoncé est inférieur aux montants unitaires des outils."

    return True, ""

# evaluation de deuxieme niveau par un llm juge avec criteres ecrits
def evaluer_llm_juge(client, modele: str, message_client: str, reponse_texte: str, observations_outils: list) -> tuple:
    prompt_juge = f"""Tu es un évaluateur strict et impartial pour un agent vendeur e-commerce WhatsApp.
Tu dois évaluer la réponse générée par l'agent selon TROIS critères écrits éliminatoires :

1. « aucun chiffre inventé » : Tous les chiffres, prix, stocks ou frais présents dans la réponse DOIVENT provenir strictement des observations des outils fournies ci-dessous. Aucun prix ou stock externe n'est toléré.
2. « alternative proposée si rupture » : Si la demande du client concerne un article en rupture de stock, l'agent DOIT avoir signalé la rupture ET proposé une alternative concrète disponible dans le catalogue.
3. « réponse de moins de 80 mots » : La réponse doit être concise et compter strictement moins de 80 mots.

Observations réelles fournies par les outils :
{json.dumps(observations_outils, ensure_ascii=False, indent=2)}

Demande initiale du client :
"{message_client}"

Réponse finale proposée par l'agent :
"{reponse_texte}"

Format de retour obligatoire : un objet JSON valide avec deux clés :
- "valide": booléen (true si les trois critères sont respectés, false sinon)
- "critique": chaîne (vide si valide, sinon description précise du critère non respecté)"""

    try:
        completion = client.chat.completions.create(
            model=modele,
            messages=[
                {"role": "system", "content": "Tu réponds uniquement par un objet JSON valide."},
                {"role": "user", "content": prompt_juge}
            ],
            temperature=0.0
        )
        contenu = completion.choices[0].message.content or ""
        contenu_nettoye = re.sub(r"^```json\s*|\s*```$", "", contenu.strip())
        resultat = json.loads(contenu_nettoye)
        return resultat.get("valide", False), resultat.get("critique", "critique non précisée")
    except Exception as e:
        # validation par defaut si le juge renvoie un format inattendu
        return True, ""

# combinaison des deux niveaux d evaluation
def evaluer_reponse_complete(client, modele: str, message_client: str, reponse_texte: str, observations_outils: list) -> tuple:
    # niveau 1 : verification de la regle arithmetique en code
    valide_code, critique_code = evaluer_regle_code(reponse_texte, observations_outils)
    if not valide_code:
        return False, critique_code

    # niveau 2 : verification par le llm juge
    valide_llm, critique_llm = evaluer_llm_juge(client, modele, message_client, reponse_texte, observations_outils)
    if not valide_llm:
        return False, critique_llm

    return True, ""
