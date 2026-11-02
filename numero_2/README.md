# Palier 2 : Fiabilité, Persistance et Multi-Agents

Ce palier renforce l'agent unitaire en le rendant transactionnel, persistant et auditable, avant d'explorer une architecture multi-agents.

## Structure Technique des Sous-Dossiers
- `donnees/` : Stockage persistant au format JSON (`stock.json`, `commandes.json`).
- `fiabilite/` : Agent fiable (Palier 2a) avec validation humaine obligatoire `[o/N]` avant enregistrement, et double niveau d'évaluation (règle arithmétique en code + LLM Juge).
- `multiagents/` : Architecture distribuée (Palier 2b) avec un Gérant orchestrateur et trois spécialistes (Vendeur, Logisticien, Rédacteur).
- `tableau.md` : Tableau d'évaluation comparative et analyse d'ingénierie.

## 1. Mécanismes de Fiabilité (Palier 2a)
1. **Validation Humaine d'Afi** : Avant d'enregistrer une commande dans `donnees/commandes.json` et de décrémenter le stock dans `donnees/stock.json`, le programme exige une validation explicite. Un refus est réinjecté comme une observation que l'agent explique au client.
2. **Double Évaluation avant Réponse** :
   - **Niveau 1 (Code)** : Vérification de la somme annoncée (articles + livraison).
   - **Niveau 2 (LLM Juge)** : Analyse des critères éliminatoires (aucun chiffre inventé, alternative si rupture, réponse < 80 mots). En cas de non-respect, la critique est réinjectée dans le contexte pour régénération.

## 2. Architecture Multi-Agents (Palier 2b)
- **Gérant (Orchestrateur)** : Coordonne la discussion sans utiliser d'outils bas niveau.
- **Vendeur** : Dédié au catalogue, au stock et à la prise de commande.
- **Logisticien** : Dédié au calcul de livraison et à la conversion de devises.
- **Rédacteur** : Sans outil, dédié au formatage du message final WhatsApp.

## Lancement des Tests

### Tester la Fiabilité (Palier 2a - Scénario Afi) :
```bash
./venv/bin/python numero_2/fiabilite/tests_fiabilite.py
```

### Tester le Multi-Agents (Palier 2b - Scénario Koffi) :
```bash
./venv/bin/python numero_2/multiagents/tests_multiagents.py
```
