import sys
from pathlib import Path

# inclusion du repertoire courant pour les imports directs
sys.path.append(str(Path(__file__).resolve().parent))

from agent import AgentVendeur

# execution des tests de validation du palier 1
def executer_tests_palier1():
    agent = AgentVendeur(max_etapes=10, max_historique=12)

    print("Debut des tests de validation pour le Palier 1")

    # test 1 : recherche de pagnes et conversion en euros
    print("\n--- Test 1 : Recherche et conversion en devises ---")
    agent.reinitialiser()
    agent.executer("Vous avez des pagnes ? Combien ça fait en euros pour ma sœur à Paris ?")

    # test 2 : demande de livraison hors zone a lome
    print("\n--- Test 2 : Zone non desservie ---")
    agent.reinitialiser()
    agent.executer("Livrez-moi à Lomé.")

    # test 3 : demande de produit en rupture de stock avec alternative
    print("\n--- Test 3 : Rupture de stock et alternative ---")
    agent.reinitialiser()
    agent.executer("C'est combien le sac en raphia ?")

    # test 4 : verification du rag avec la base de connaissances
    print("\n--- Test 4 (RAG) : Conseils d'entretien du wax ---")
    agent.reinitialiser()
    agent.executer("Comment je dois laver mon pagne wax pour ne pas abîmer les couleurs ?")

if __name__ == "__main__":
    executer_tests_palier1()
