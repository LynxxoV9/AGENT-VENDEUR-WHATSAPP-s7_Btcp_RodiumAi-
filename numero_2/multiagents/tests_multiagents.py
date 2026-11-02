import sys
from pathlib import Path

# inclusion du repertoire multiagents dans sys path
sys.path.append(str(Path(__file__).resolve().parent))

from gerant import EquipeBoutique

# test du scenario koffi a porto-novo
def tester_scenario_koffi():
    print("Debut du test Multi-Agents (Palier 2b) : Scenario Koffi")

    equipe = EquipeBoutique(max_etapes=10)
    demande = "Je suis Koffi à Porto-Novo. Combien me coûtent 3 pots de beurre de karité livrés, et ça fait combien en nairas ?"

    reponse = equipe.executer(demande)

    print("\nReponse finale obtenue :")
    print(reponse)

if __name__ == "__main__":
    tester_scenario_koffi()
