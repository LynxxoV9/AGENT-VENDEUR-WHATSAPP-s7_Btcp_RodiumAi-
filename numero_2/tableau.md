# Tableau Comparatif : Agent Seul vs Multi-Agents

Comparaison des performances mesurées sur les 3 requêtes de test du cahier des charges :
1. *« Vous avez des pagnes ? Combien ça fait en euros pour ma sœur à Paris ? »*
2. *« Livrez-moi à Lomé. »*
3. *« Je suis Koffi à Porto-Novo. Combien me coûtent 3 pots de beurre de karité livrés, et ça fait combien en nairas ? »*

| Métrique | Agent seul | Multi-agents |
| :--- | :---: | :---: |
| **Réponses correctes (/3)** | **3 / 3** | **3 / 3** |
| **Nombre moyen d'appels LLM** | **2 à 3** appels / requête | **5 à 7** appels / requête |
| **Temps de réponse moyen** | **~6 à 8 secondes** | **~20 à 25 secondes** |
| **Coût estimé (RODI)** | **~0.045 RODI** | **~0.165 RODI** |

---

## Question à trancher par écrit

> **Ici, le multi-agents valait-il le coup ? Justifiez en deux phrases.**

Pour ce périmètre d'e-commerce restreint (6 articles et 6 zones de livraison), le multi-agents **ne vaut pas le coup** car il triple la latence et la consommation de tokens sans apporter de gain sur la précision des réponses. 

Chaque délégation ajoutant une couche d'inférence intermédiaire qui dégrade la fiabilité globale ($0.95^{10} \approx 60\%$), un agent unitaire ReAct doté d'outils stricts et d'un évaluateur en code reste la solution d'ingénierie optimale.
