import sys
import time
from pathlib import Path

# inclusion des chemins des agents
sys.path.append(str(Path(__file__).resolve().parent.parent / "numero_1"))
sys.path.append(str(Path(__file__).resolve().parent / "fiabilite"))
sys.path.append(str(Path(__file__).resolve().parent / "multiagents"))

from agent import AgentVendeur
from gerant import EquipeBoutique

# benchmark comparatif entre agent unitaire et multi agents
def executer_comparaison():
    demandes_test = [
        "Vous avez des pagnes ? Combien ça fait en euros pour ma sœur à Paris ?",
        "Livrez-moi à Lomé.",
        "Je suis Koffi à Porto-Novo. Combien me coûtent 3 pots de beurre de karité livrés, et ça fait combien en nairas ?"
    ]

    print("Debut du benchmark comparatif : Agent Seul vs Multi-Agents")

    # evaluation de l agent seul
    print("\n--- Evaluation Agent Seul ---")
    agent_seul = AgentVendeur()
    debut_seul = time.time()
    for d in demandes_test:
        agent_seul.reinitialiser()
        agent_seul.executer(d, afficher_trace=False)
    temps_seul = time.time() - debut_seul
    temps_moyen_seul = round(temps_seul / len(demandes_test), 2)

    # evaluation de l equipe multi agents
    print("\n--- Evaluation Multi-Agents ---")
    equipe = EquipeBoutique()
    debut_multi = time.time()
    for d in demandes_test:
        equipe.reinitialiser()
        equipe.executer(d, afficher_trace=False)
    temps_multi = time.time() - debut_multi
    temps_moyen_multi = round(temps_multi / len(demandes_test), 2)

    print(f"\nResultats :")
    print(f"Agent Seul : Temps moyen = {temps_moyen_seul} s")
    print(f"Multi-Agents : Temps moyen = {temps_moyen_multi} s")

if __name__ == "__main__":
    executer_comparaison()
