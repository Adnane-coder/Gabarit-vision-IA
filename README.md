# Gabarit Vision IA

### Système intelligent de contrôle de conformité des pièces de patron textile par Deep Learning

**Projet de fin d'études — Ingénierie IA & Data Science — SARTEX**

> Automatiser le contrôle dimensionnel de pièces de patron textile à partir de tracés industriels, en remplaçant une approche classique basée sur OpenCV/Canny par un pipeline de segmentation **U-Net**.

---

## 🎯 Présentation du projet

**Gabarit Vision IA** est un système de vision par ordinateur développé pour **SARTEX**, entreprise industrielle spécialisée dans le textile.

L'objectif est d'automatiser le contrôle de conformité des pièces de patron après découpe.

À partir de tracés PDF issus de **Gerber AccuMark**, le système :

* détecte automatiquement les différentes pièces ;
* segmente les pièces à l'aide d'un modèle **U-Net** ;
* mesure leurs dimensions ;
* compare chaque pièce avec sa référence ;
* détecte les pièces manquantes ou inattendues ;
* génère automatiquement un verdict de conformité.

Le système prend actuellement en charge une tolérance dimensionnelle de **±3 cm**.

### Pourquoi utiliser le Deep Learning ?

L'approche historique basée sur les contours **Canny + OpenCV** devient fragile lorsque plusieurs tracés sont imbriqués ou connectés.

Le projet explore donc une approche basée sur la **segmentation sémantique par Deep Learning**, avec un modèle U-Net entraîné sur les données réelles disponibles chez SARTEX.

---

# 🏭 Contexte industriel

Les pièces de patron sont générées à partir de fichiers PDF correspondant à des exports vectoriels **1:1 de Gerber AccuMark**.

Le contrôle manuel ou basé uniquement sur des contours classiques peut devenir difficile lorsque :

* plusieurs pièces sont proches ou imbriquées ;
* les frontières des pièces sont connectées ;
* les tracés présentent des variations ou des artefacts ;
* certaines pièces sont absentes ou apparaissent de manière inattendue.

Le système développé cherche à transformer ce contrôle en un **pipeline automatisé, mesurable et reproductible**.

---

# 🧠 Architecture globale

```text
                    ┌──────────────────────┐
                    │   Tracé PDF 1:1      │
                    │   Gerber AccuMark    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Prétraitement PDF    │
                    │ + génération patches │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │       U-Net          │
                    │ Segmentation 2 classes│
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Reconstruction des   │
                    │ pièces détectées     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Mesure dimensionnelle│
                    │       en cm          │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Appariement avec les │
                    │ références attendues │
                    └──────────┬───────────┘
                               │
                               ▼
              ┌─────────────────────────────────┐
              │          VERDICT FINAL           │
              │                                  │
              │  ✓ CONFORME                     │
              │  ✗ NON CONFORME                 │
              │  ⚠ MANQUANTE                    │
              │  ⚠ INATTENDUE                   │
              └─────────────────────────────────┘
```

---

# 🔬 Pipeline Machine Learning

Le développement est organisé dans les notebooks `01` à `11`.

### 01–02 — Exploration & construction des références

Analyse des PDFs industriels et construction de la table de référence contenant les dimensions attendues pour chaque pièce.

### 04–05 — Dataset & segmentation

Génération :

* des masques de segmentation ;
* des frontières et régions intérieures ;
* des patches avec chevauchement ;
* des données augmentées pour l'entraînement.

Le dataset disponible comprend **125 pièces annotées provenant de 4 tracés de référence**.

### 06–08 — Entraînement U-Net

Le modèle utilisé est un **U-Net avec encodeur ResNet18** et deux classes de segmentation.

Caractéristiques principales :

| Élément              | Configuration                |
| -------------------- | ---------------------------- |
| Architecture         | U-Net                        |
| Encoder              | ResNet18                     |
| Classes              | 2                            |
| Paramètres           | ~14,3 M                      |
| Validation           | Leave-One-Out                |
| Nombre de tracés     | 4                            |
| GPU de développement | NVIDIA GTX 1650 Max-Q 4 GB   |
| Mixed Precision      | Désactivée (`USE_AMP=False`) |

La validation est réalisée en **leave-one-out**, permettant de tester la capacité du modèle à généraliser d'un tracé à un autre.

---

# ⚔️ Canny vs U-Net

Une comparaison directe avec l'approche historique basée sur **OpenCV/Canny** a été réalisée.

Les résultats montrent que l'approche U-Net améliore notamment la segmentation et le comptage des pièces.

Cependant, l'analyse met également en évidence un point important :

> La segmentation U-Net peut encore produire des fragmentations au niveau des frontières de tuiles, ce qui influence certaines mesures dimensionnelles.

Cette observation a conduit à l'utilisation de **tuiles chevauchantes** et à l'agrégation des probabilités.

L'approche Canny reste par ailleurs compétitive pour certaines mesures dimensionnelles spécifiques.

---

# 🔄 Pipeline de conformité

Le pipeline complet est implémenté dans :

```text
api/app/models/conformity_pipeline.py
```

Le traitement suit la chaîne :

```text
PDF
 ↓
Prétraitement
 ↓
Découpage en tuiles
 ↓
Inférence U-Net
 ↓
Agrégation des probabilités
 ↓
Reconstruction des pièces
 ↓
Mesure en cm
 ↓
Appariement 1-to-1
 ↓
Contrôle de tolérance
 ↓
Verdict
```

### Stratégie de tuilage

Les images sont traitées avec :

* stride de **128 pixels** ;
* chevauchement de **50 %** ;
* moyenne des probabilités entre les tuiles.

Cette stratégie permet de réduire les artefacts apparaissant aux frontières des tuiles.

---

# 📊 Verdict de conformité

Chaque pièce détectée est comparée à sa référence.

Le système peut produire quatre états :

| Verdict           | Signification                                           |
| ----------------- | ------------------------------------------------------- |
| 🟢 `CONFORME`     | La pièce respecte la tolérance attendue                 |
| 🔴 `NON CONFORME` | Les dimensions dépassent la tolérance                   |
| 🟠 `MANQUANTE`    | Une pièce attendue n'a pas été détectée                 |
| 🔵 `INATTENDUE`   | Une pièce non présente dans la référence a été détectée |

Les pièces de référence non appariées sont conservées dans le calcul de conformité afin d'éviter de surestimer artificiellement le taux global.

---

# 🧪 Validation du pipeline

Le pipeline a été testé de bout en bout sur les données disponibles.

### Validation actuelle

* ✅ 4 folds de validation ;
* ✅ pipeline ML complet ;
* ✅ pipeline PDF → verdict ;
* ✅ comparaison Canny / U-Net ;
* ✅ tests d'injection de défauts ;
* ✅ détection de défauts synthétiques validée sur **3/3 tests**.

Le notebook `11` permet notamment de simuler des anomalies dimensionnelles afin de vérifier que le système détecte correctement les écarts introduits artificiellement.

---

# 🖥️ Architecture logicielle

Le projet est organisé autour de trois composants principaux :

```text
                     Gabarit Vision IA
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
          ML Pipeline     FastAPI       React
              │             │             │
              │             │             │
              ▼             ▼             ▼
          U-Net +        Backend       Dashboard
          notebooks      REST API      utilisateur
```

### Backend — FastAPI

Le backend expose le pipeline de conformité via une API REST.

Il possède deux modes :

```text
MOCK MODE
   ↓
Données simulées
   ↓
Développement rapide du frontend


REAL MODE
   ↓
Pipeline U-Net réel
   ↓
Résultats de conformité
```

### Frontend — React / Vite

Le dashboard permet actuellement de :

1. sélectionner un tracé ;
2. lancer une inspection ;
3. communiquer avec l'API ;
4. afficher les résultats ;
5. consulter le verdict de chaque pièce.

---

# 📁 Structure du projet

```text
gabarit-vision-ia/
│
├── notebooks/
│   └── 01 → 11
│       Exploration → Dataset → Training → Validation
│
├── src/
│   └── Code ML réutilisable
│
├── data/
│   └── PDFs, annotations, patches et résultats
│
├── models/
│   └── saved/
│       Checkpoints U-Net
│
├── tools/
│   └── Outils d'annotation
│
├── api/
│   ├── app/
│   ├── tests/
│   └── README.md
│
├── dashboard/
│   ├── src/
│   └── README.md
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

# ⚙️ Installation

## 1. Environnement Machine Learning

Depuis la racine du projet :

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Puis :

```bash
pip install -r requirements.txt
```

> Un GPU NVIDIA est recommandé pour l'entraînement des modèles. Le reste du pipeline peut fonctionner sur CPU.

Le développement initial a été réalisé sur une **NVIDIA GTX 1650 Max-Q 4 GB**.

---

# 🚀 Lancer le backend FastAPI

```bash
cd api
```

Créer l'environnement :

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

Créer le fichier d'environnement :

```bash
copy .env.example .env
```

Puis lancer l'API :

```bash
uvicorn app.main:app --reload
```

Documentation interactive :

```text
http://localhost:8000/docs
```

Pour comprendre les différents modes et endpoints :

→ consulter [`api/README.md`](api/README.md)

---

# 💻 Lancer le dashboard

Depuis le dossier `dashboard` :

```bash
cd dashboard
```

Installer les dépendances :

```bash
npm install
```

Créer l'environnement :

```bash
copy .env.example .env
```

Puis :

```bash
npm run dev
```

Par défaut, le dashboard peut fonctionner avec des données mockées.

Pour utiliser le backend réel, configurer notamment :

```text
VITE_API_BASE_URL
VITE_USE_MOCK=false
```

Plus de détails :

→ consulter [`dashboard/README.md`](dashboard/README.md)

---

# 🧩 Points techniques importants

### Détection des pièces

Une approche basée uniquement sur :

```python
cv2.findContours(...)
```

avec :

```text
RETR_EXTERNAL
```

s'est révélée insuffisante pour certains tracés imbriqués.

L'approche retenue utilise notamment :

```python
cv2.connectedComponentsWithStats(...)
```

sur une représentation adaptée des contours.

---

### Gestion des artefacts de tuilage

Le traitement par patches peut créer des fragmentations aux frontières.

La solution retenue combine :

```text
50 % overlap
        +
moyenne des probabilités
        +
reconstruction globale
```

Une fermeture morphologique a également été testée avec différents paramètres, mais n'a pas été retenue car elle dégradait les résultats observés.

---

### Échelle des mesures

Les PDFs utilisés sont des exports vectoriels **1:1**.

La conversion des dimensions ne nécessite donc pas actuellement de référence physique de calibration.

Cette hypothèse changera lors du passage à une capture caméra.

---

### Extraction des informations PDF

**PyMuPDF (`fitz`)** est utilisé pour l'extraction des textes et libellés.

Il s'est montré plus adapté que `pdfplumber` pour les libellés pivotés présents dans les PDFs issus de Gerber AccuMark.

---

# 📝 Organisation des environnements

Le projet utilise plusieurs environnements selon le composant :

```text
Projet
│
├── .venv/
│   └── ML + notebooks + src
│
├── api/.venv/
│   └── FastAPI + dépendances backend
│
└── dashboard/node_modules/
    └── dépendances React
```

Les environnements locaux et fichiers sensibles sont exclus du dépôt via `.gitignore`.

---

# 🛣️ Roadmap

### ✅ Déjà réalisé

* [x] Analyse des tracés PDF industriels
* [x] Construction des références dimensionnelles
* [x] Annotation des pièces
* [x] Génération du dataset
* [x] Entraînement U-Net
* [x] Validation Leave-One-Out
* [x] Comparaison Canny / U-Net
* [x] Pipeline de conformité complet
* [x] Injection de défauts synthétiques
* [x] Backend FastAPI
* [x] Mode Mock / Real
* [x] Dashboard React
* [x] Communication Frontend ↔ Backend

### 🚧 Prochaines étapes

* [ ] Intégration de la capture caméra Raspberry Pi
* [ ] Implémentation complète de `CameraInterface`
* [ ] Calibration automatique par marqueurs ArUco
* [ ] Adaptation du pipeline aux images caméra
* [ ] Validation sur des conditions réelles de production
* [ ] Déploiement du système sur matériel industriel

---

# 🧹 Nettoyage et qualité du dépôt

Le dépôt a également fait l'objet d'un nettoyage afin de le rendre reproductible et portable.

### Nettoyages réalisés

* suppression des `__pycache__/` ;
* suppression des fichiers `*.pyc` ;
* suppression de `dashboard/node_modules/` ;
* suppression de dossiers parasites ;
* correction de noms de fichiers corrompus ;
* remplacement des chemins Windows codés en dur ;
* ajout de configurations VS Code pour les 4 tracés ;
* mise à jour des dépendances ML ;
* mise à jour des README backend et frontend ;
* ajout du `.gitignore` racine ;
* ajout de ce README principal.

Les fichiers `__init__.py` et `.gitkeep` nécessaires au fonctionnement et à la structure du dépôt ont volontairement été conservés.

---

# 📌 État actuel du système

```text
                    PDF Gerber AccuMark
                             │
                             ▼
                    ┌─────────────────┐
                    │   ML Pipeline   │
                    │     U-Net       │
                    └────────┬────────┘
                             │
                             ▼
                    Analyse des pièces
                             │
                             ▼
                    Contrôle dimensionnel
                             │
                             ▼
                    FastAPI Backend
                             │
                             ▼
                    React Dashboard
                             │
                             ▼
                  Résultats de conformité
```

Le système fonctionne actuellement sur des **tracés PDF vectoriels 1:1**.

La prochaine évolution majeure consiste à remplacer cette entrée par une **capture caméra Raspberry Pi**, nécessitant notamment une calibration physique et une adaptation du pipeline de vision.

---

# 👨‍💻 Auteur

**Adnane Ben Ammar**

Étudiant en **Ingénierie IA & Data Science**

Réalisé pour **SARTEX**.

**Domaines :**

`Computer Vision` · `Deep Learning` · `U-Net` · `Python` · `PyTorch` · `OpenCV` · `FastAPI` · `React` · `Data Science`

---
