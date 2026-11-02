# Palier 1 : Agent Vendeur Unitaire (ReAct)

## Objectif
Mettre en place un agent vendeur autonome pour la boutique d'Afi au marché Dantokpa, capable d'enchaîner plusieurs actions réfléchies selon la boucle : **penser -> agir -> observer -> évaluer**.

## Modèle et Configuration
- **Modèle** : `google/gemini-3.8-flash` via l'API RodiumAI (`https://api.rodiumai.io/v1`).
- **Température** : `0.1` (déterministe, zéro hallucination sur les prix et stocks).
- **Nombre maximal d'étapes (`max_steps`)** : 10.
- **Taille de contexte glissant** : 12 derniers messages.

## Outils Développés
1. `chercher_produits(mot_cle)` : recherche textuelle dans le catalogue. Erreur : `aucun produit pour X`.
2. `verifier_stock(reference)` : vérifie la disponibilité d'une référence. Erreur : `référence inconnue`.
3. `frais_livraison(zone)` : renvoie les frais et délais. Erreur : `zone non desservie` avec la liste des zones autorisées.
4. `convertir_devise(montant_fcfa, devise_cible)` : conversion en direct via l'API de taux réels (avec repli de parités). Erreur : `devise non prise en charge`.
5. `creer_commande(reference, quantite, zone)` : enregistre la commande. Erreur : `stock insuffisant pour X`.
6. `consulter_guide_boutique(sujet)` : outil de RAG sur le guide textile, entretien et politique de retours.

## Lancement des Tests
```bash
./venv/bin/python numero_1/tests.py
```
