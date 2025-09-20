# 🚚 Application de gestion de matériel (inspirée OTAN)

Cette application Python met en œuvre une gestion de bout en bout du matériel :
réception en entrepôt, transport, réparation locale ou en usine, distribution en
magasin et élimination. Elle s'appuie sur les classes logistiques OTAN et
produit les documents nécessaires à chaque étape.

## ⚙️ Fonctionnalités principales

- Modélisation objet des matériels, lieux, ordres de transport et de réparation.
- Gestion du stock multi-sites avec suivi des mouvements.
- Génération de documents logistiques : réception, transport, réparation,
  distribution magasin, élimination.
- Procédure de flux logistique codifiée en 10 étapes inspirée de la supply chain
  OTAN.
- Interface CLI simple pour manipuler le cycle de vie complet.

## ▶️ Démarrer l'application

```bash
python main.py
```

Un jeu de données exemple est chargé automatiquement (groupe électrogène,
plusieurs sites). Le menu CLI permet :

1. Consulter un matériel (NSN, condition, historique).
2. Réceptionner du matériel en entrepôt.
3. Planifier un transport (création mission + document).
4. Clore un transport (mise à jour stock destination).
5. Créer un ordre de réparation (local ou usine).
6. Clore un ordre de réparation.
7. Visualiser l'état de stock par site.
8. Afficher la procédure logistique OTAN simplifiée.
9. Lister les documents par type.

## 📄 Procédure OTAN simplifiée

La procédure implémente les codes SC-01 à SC-10 : codification, réception,
stockage, transport (code MVT), transit, réparations locales (REP-L) et usines
(REP-F), distribution (DIST), gestion documentaire, élimination (DISPO). Chaque
étape rappelle la classe OTAN correspondante et les documents requis.

## 📂 Structure

```
modules/
├── entities.py         # Entités métiers : matériel, lieux, documents…
├── logistics_flow.py   # Gestionnaire de stock et de flux
└── procedure.py        # Procédure OTAN simplifiée
main.py                 # Interface CLI
```

## ✅ Dépendances

Aucune dépendance externe n'est requise (standard library uniquement).
