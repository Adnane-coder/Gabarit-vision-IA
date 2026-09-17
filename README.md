# gabarit-vision-ia

Système de contrôle de conformité des tracés de patrons (pièces de vêtement
découpées) pour **SARTEX**, basé sur une segmentation par deep learning
(U-Net) plutôt que la chaîne classique OpenCV/Canny historique.

Projet de fin d'études (PFE) — Ingénierie IA & Data Science.

## Le problème

SARTEX découpe des pièces de patron à partir de tracés PDF (exports vectoriels
1:1 issus de Gerber AccuMark). Il faut vérifier que chaque pièce coupée
respecte les dimensions de référence à **±3 cm** près, pièce par pièce, et
signaler les pièces manquantes ou inattendues. L'ancienne approche (contours
Canny) est fragile sur les tracés imbriqués. Ce projet la remplace par un
pipeline U-Net entraîné sur les 4 tracés de référence disponibles (125 pièces
annotées au total).

## Vue d'ensemble du dépôt

```
gabarit-vision-ia/
├── notebooks/     Exploration → entraînement → pipeline de conformité (01 à 11, dans l'ordre)
├── src/           Code réutilisable importé par les notebooks et par l'API
├── data/          PDFs de référence, masques/patches générés, annotations, résultats
├── models/saved/  Checkpoints U-Net entraînés (4 folds leave-one-out, ~55 Mo chacun)
├── tools/         Outil d'annotation HTML (un par tracé)
├── api/           Backend FastAPI (mode mock ↔ pipeline réel)
└── dashboard/     Frontend React/Vite (sélection tracé → inspection → verdict par pièce)
```

Chaque sous-dossier a son propre README détaillé : [`api/README.md`](api/README.md)
et [`dashboard/README.md`](dashboard/README.md). Celui-ci donne la vue
d'ensemble et la marche à suivre pour tout faire tourner de zéro.

## Pipeline (résumé, voir `notebooks/`)

1. **Exploration & référence** (`01`–`02`) — lecture des PDFs 1:1, construction
   de la table de dimensions de référence par pièce.
2. **Génération des masques / dataset** (`04`–`05`) — masques frontière/intérieur
   par pièce, découpage en patches avec chevauchement (tiles), augmentation.
3. **Entraînement U-Net** (`06`–`08`) — encodeur ResNet18, 2 classes,
   ~14,3M paramètres (`segmentation-models-pytorch`), validation en
   leave-one-out sur les 4 tracés. `USE_AMP=False` (voir
   [`technical-learnings`](#notes-techniques-clés) — la précision mixte
   provoque des NaN avec un décodeur non pré-entraîné).
4. **Comparaison Canny vs U-Net** (`09`) — U-Net gagne en IoU/Dice et comptage
   de pièces ; Canny reste étonnamment compétitif sur la conformité
   dimensionnelle pure (fragmentation résiduelle du U-Net sur les tuiles).
5. **Pipeline de conformité bout-en-bout** (`10`) — PDF → inférence U-Net par
   tuiles chevauchantes (stride 128, 50%) → mesure des pièces en cm →
   appariement glouton un-à-un → verdict (`CONFORME` / `NON CONFORME` /
   `MANQUANTE` / `INATTENDUE`). Porté tel quel dans
   `api/app/models/conformity_pipeline.py`.
6. **Injection de défauts synthétiques** (`11`) — validation que le pipeline
   détecte bien des anomalies dimensionnelles (ex. +5,3% de taille).

## Installation

### 1. Environnement ML (notebooks + `src/`)

```bash
python -m venv .venv
source .venv/bin/activate      # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

> GPU recommandé pour l'entraînement (`06`–`07`) ; le reste tourne sur CPU.
> Ce dépôt a été développé/entraîné sur une GTX 1650 Max-Q (4 Go VRAM).

### 2. Backend FastAPI (`api/`)

```bash
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Swagger : http://localhost:8000/docs. Détails complets (bascule mock ↔ réel,
endpoints, tests) dans [`api/README.md`](api/README.md).

### 3. Dashboard React (`dashboard/`)

```bash
cd dashboard
npm install
cp .env.example .env
npm run dev
```

Par défaut le dashboard tourne en données mockées ; branchez-le sur l'API
réelle via `VITE_API_BASE_URL` / `VITE_USE_MOCK=false` (détails dans
[`dashboard/README.md`](dashboard/README.md)).

## Notes techniques clés

- **Topologie des pièces** : `findContours` + `RETR_EXTERNAL` échoue sur les
  tracés imbriqués où toutes les frontières forment un seul réseau connecté —
  `cv2.connectedComponentsWithStats` sur une image de contours inversée est
  l'approche correcte.
- **Artefacts de tuilage** : le chevauchement à 50% avec moyennage des
  probabilités atténue la fragmentation en bord de tuile ; la fermeture
  morphologique a été testée (3px et 7px) et rejetée — elle dégrade les
  résultats.
- **Appariement de conformité** : les pièces de référence non appariées
  comptent comme non conformes au dénominateur — les ignorer biaiserait le
  taux de conformité global.
- **Échelle** : les PDFs sont de vrais exports vectoriels 1:1 — pas besoin
  d'objet de calibration pour la lecture des dimensions (contrairement au
  futur déploiement caméra, voir plus bas).
- **Extraction de texte PDF** : PyMuPDF (`fitz`) extrait correctement les
  libellés pivotés des PDFs AccuMark ; `pdfplumber` en rate une part
  significative.
- **Environnement notebook** : les `pip install` en terminal ne se propagent
  pas toujours au kernel VS Code — utiliser
  `{sys.executable} -m pip install ...` directement dans une cellule.

## État actuel / prochaines étapes

- [x] Pipeline ML complet et validé de bout en bout (4 folds, tests de
      détection de défaut 3/3)
- [x] Backend FastAPI avec bascule mock/réel propre, testé
- [x] Frontend React branché sur l'API réelle (sélecteur de tracé → run →
      tableau de verdicts par pièce)
- [ ] Déploiement physique : remplacer l'entrée PDF par une capture caméra
      Raspberry Pi (`api/app/hardware/raspberry_pi.py`, actuellement un stub
      derrière `CameraInterface`)
- [ ] Calibration par marqueurs ArUco pour dériver l'échelle une fois hors du
      contexte "PDF vectoriel 1:1" (nécessaire dès que l'entrée devient une
      photo caméra)

## Changelog de ce nettoyage

- Suppression de `__pycache__/`, `*.pyc`, `dashboard/node_modules/`
  (régénérable via `npm install`) et de deux dossiers vides parasites créés
  par une expansion d'accolades shell ratée (`api/app/{api`,
  `dashboard/src/{components`).
- Renommage de deux fichiers `data/processed/*.png` dont le nom était corrompu
  (encodage d'URL/caractères mal interprété) en noms lisibles.
- `.vscode/launch.json` : remplacement du chemin Windows personnel codé en dur
  par `${workspaceFolder}` (portable), et ajout des 4 configurations
  (une par tracé) au lieu d'une seule.
- `requirements.txt` (racine) : ajout de `torch`, `segmentation-models-pytorch`,
  `albumentations`, `pandas` — utilisés par `src/` et les notebooks 06-11 mais
  absents du fichier d'origine.
- `dashboard/README.md` : structure de composants et contrat JSON mis à jour
  (documentaient encore l'ancien flux caméra/phases générique, remplacé par
  le vrai workflow de conformité tracé → pièce).
- `api/README.md` : numérotation des sections corrigée (un saut 9 → 12).
- Ajout de ce README racine, d'un `.gitignore` racine (absent auparavant —
  seul `api/.gitignore` existait, sans couvrir `node_modules/`, les
  checkpoints, etc.) et de ce changelog.
- Les fichiers `__init__.py` vides et `api/models/saved/.gitkeep` ont été
  **conservés** : ce sont des marqueurs Python/Git légitimes, pas des
  fichiers vides à nettoyer (les supprimer casserait les imports du package
  et l'existence du dossier `models/saved/` sous Git).

## Auteur

Projet de fin d'études — Ingénierie IA & Data Science, pour SARTEX.
