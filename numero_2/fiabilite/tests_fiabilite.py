import sys
from pathlib import Path

# inclusion du repertoire fiabilite dans le sys path
sys.path.append(str(Path(__file__).resolve().parent))

from agent_fiable import AgentVendeurFiable
from outils_fiables import configurer_hook_validation
from gestionnaire_stock import charger_stock, charger_commandes

# fonction de test simulant le scenario afi complet avec refus puis acceptation
def tester_scenario_fiabilite():
    agent = AgentVendeurFiable(max_etapes=10, max_historique=12)

    print("Debut du test de fiabilite (Palier 2a) : Scenario Afi")

    # phase 1 : demande initiale avec rupture et calcul du total
    message_client = "Je m'appelle Afi. Je veux 2 robes en wax et 1 sac en raphia, livrés à Calavi."
    reponse1 = agent.executer(message_client)

    # phase 2 : confirmation du client avec premier refus humain
    print("\n--- Test du Refus Humain ---")
    # configuration du hook pour simuler un refus [o/N] -> Non
    configurer_hook_validation(lambda prod, qte, zone: False)

    reponse2 = agent.executer("Oui je confirme pour les 2 robes en wax à Calavi.")

    # verification que le stock n a pas change et qu aucune commande n est enregistree
    stock_apres_refus = charger_stock()
    robes_refus = next(p for p in stock_apres_refus if p["reference"] == "P05")
    commandes_refus = charger_commandes()

    print(f"Stock Robe P05 après refus : {robes_refus['stock']} (attendu: 5)")
    print(f"Nombre de commandes après refus : {len(commandes_refus)} (attendu: 0)")
    assert robes_refus["stock"] == 5, "Le stock ne doit pas baisser après un refus"
    assert len(commandes_refus) == 0, "Aucune commande ne doit être enregistrée après un refus"

    # phase 3 : validation humaine accordee
    print("\n--- Test de l'Accord Humain ---")
    # configuration du hook pour simuler une validation [o/N] -> Oui
    configurer_hook_validation(lambda prod, qte, zone: True)

    reponse3 = agent.executer("Afi a donné son feu vert, valide la commande !")

    # verification de la decrementation du stock et de l ecriture json
    stock_apres_accord = charger_stock()
    robes_accord = next(p for p in stock_apres_accord if p["reference"] == "P05")
    commandes_accord = charger_commandes()

    print(f"Stock Robe P05 après accord : {robes_accord['stock']} (attendu: 3)")
    print(f"Nombre de commandes après accord : {len(commandes_accord)} (attendu: 1)")
    assert robes_accord["stock"] == 3, "Le stock doit être décrémenté de 2"
    assert len(commandes_accord) == 1, "La commande doit être enregistrée dans commandes.json"

    print("\nTest de fiabilite (Palier 2a) reussi avec succes !")

if __name__ == "__main__":
    tester_scenario_fiabilite()
