# AI Inspection Platform — Backend (FastAPI)

Backend en mode **MOCK** : caméra et modèle IA sont simulés, mais l'architecture
(routes, schémas, interfaces) est celle qui restera en place une fois le
Raspberry Pi et le modèle réel branchés.

## 1. Architecture

```
api/
└── app/
    ├── main.py               Assemble l'app, CORS, wiring des services, gestion d'erreurs
    ├── api/
    │   ├── routes/            health, camera, ai, inspection, system
    │   ├── router.py          Agrège toutes les routes
    │   └── dependencies.py    Injection des services via app.state
    ├── core/
    │   ├── config.py          Settings (pydantic-settings, lit .env)
    │   ├── logging.py         Config du logging (remplace print())
    │   ├── security.py        Placeholder (pas d'auth pour l'instant)
    │   └── exceptions.py      Erreurs métier → réponses API cohérentes
    ├── schemas/                Contrats Pydantic (camera, ai, inspection, system, common)
    ├── services/               Logique métier (camera_service, ai_service, inspection_service)
    ├── models/
    │   ├── model_manager.py    Cycle de vie du modèle (chargement unique, état)
    │   └── inference.py        Interface AIService + RealAIService (stub)
    ├── hardware/
    │   ├── camera.py           Interface CameraInterface
    │   ├── raspberry_pi.py     RaspberryPiCamera (stub, hardware pas encore dispo)
    │   └── gpio.py             Interface GPIO (stub, pour LEDs/capteurs futurs)
    └── mocks/
        ├── camera_mock.py      MockCamera
        └── ai_mock.py          MockAIService
```

Aucune logique métier dans les routes : chaque route appelle un service, qui
appelle une interface (caméra ou IA). Les routes ne savent pas si elles parlent
à un mock ou au vrai matériel.

## 2. Installation

```bash
cd api
python -m venv .venv
# Windows : .venv\Scripts\activate
# macOS/Linux : source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Configuration

```bash
cp .env.example .env
```

Variables principales (voir `.env.example`) : `MOCK_MODE`, `CAMERA_ENABLED`,
`AI_ENABLED`, `MODEL_PATH`, `CORS_ORIGINS`. Ne jamais coder ces valeurs en dur
ailleurs dans le code.

## 4. Lancer le serveur

```bash
uvicorn app.main:app --reload
```

Swagger : http://localhost:8000/docs

## 5. Endpoints disponibles

| Méthode | Route                    | Description                          |
|---------|--------------------------|---------------------------------------|
| GET     | `/api/v1/health`         | Statut du backend                     |
| GET     | `/api/v1/system/info`    | Config courante (mode, env, flags)    |
| GET     | `/api/v1/camera/status`  | Statut caméra (mock)                  |
| POST    | `/api/v1/camera/capture` | Capture d'une image (mock)            |
| GET     | `/api/v1/ai/status`      | Statut du modèle IA (mock)            |
| POST    | `/api/v1/inspection/run` | Inspection complète bout-en-bout      |

## 6. Mode MOCK → REAL

Un seul point de bascule : `app/main.py`, dans `lifespan()`.

```python
camera_backend = RaspberryPiCamera(...) if settings.CAMERA_ENABLED else MockCamera()
ai_backend = RealAIService(...) if settings.AI_ENABLED else MockAIService()
```

Passer `CAMERA_ENABLED=true` / `AI_ENABLED=true` dans `.env` active les vraies
implémentations — à condition qu'elles soient réellement écrites (elles lèvent
`NotImplementedError` pour l'instant, volontairement, tant que le hardware et
les poids du modèle ne sont pas disponibles). Aucune route, aucun schéma, et
rien côté React n'a besoin de changer.

## 7. Architecture caméra

`CameraInterface` (dans `hardware/camera.py`) définit le contrat
(`connect`, `disconnect`, `capture`, `get_status`). `MockCamera` l'implémente
pour l'instant ; `RaspberryPiCamera` est prête à être complétée quand la
caméra Raspberry Pi sera branchée.

## 8. Architecture IA

`AIService` (dans `models/inference.py`) définit `analyze()`. `MockAIService`
retourne des résultats simulés réalistes. `RealAIService` est un stub qui
attend `ModelManager` pour charger les poids réels — actuellement
`ModelManager` ne charge rien tant que `AI_ENABLED=false` ou que
`MODEL_PATH` ne contient rien.

## 9. Préparation Raspberry Pi

Rien dans `app/api/` ou `app/services/` ne dépend directement du matériel :
tout passe par `hardware/`. Le déploiement futur consistera à implémenter
`RaspberryPiCamera` et éventuellement `gpio.py`, puis à activer
`CAMERA_ENABLED=true`.

## 10. Mode réel (pipeline de conformité)

`RealAIService` (dans `app/models/inference.py`) fait tourner le vrai pipeline
porté depuis `notebooks/10_pipeline_conformite.ipynb` — PDF → segmentation
U-Net → mesure → appariement glouton → verdict par pièce. Le code a été copié
et testé pour reproduire exactement le comportement validé dans
`notebooks/03_conformity_check.ipynb` (test de cohérence + test de détection
de défaut).

**Différence importante avec le reste de l'API** : le pipeline réel travaille
sur un **tracé PDF connu** (Tracee1-4), pas sur une image caméra générique.
`InspectionRequest` a donc un champ `tracee` (ex: `"Tracee1"`) — en mode mock
il est ignoré, en mode réel il est obligatoire.

Pour activer le mode réel :

```env
MOCK_MODE=false
AI_ENABLED=true
CHECKPOINTS_DIR=../models/saved
REFERENCE_TABLE_PATH=../data/processed/reference_dimensions.json
TRACEES_PDF_DIR=../data/raw/reference
ANNOTATIONS_DIR=../data/processed
RESULTS_DIR=../data/results
```

Ces chemins par défaut supposent que `api/` est au même niveau que `models/`
et `data/` (comme dans ton arborescence `gabarit-vision-ia/`).

```bash
pip install -r requirements.txt   # installe aussi torch, opencv, smp, PyMuPDF
uvicorn app.main:app --reload
```

Puis dans Swagger, `POST /api/v1/inspection/run` avec :

```json
{ "tracee": "Tracee1" }
```

La réponse inclut, en plus des champs habituels, le rapport détaillé par
pièce (`n_conformes`, `n_non_conformes`, `n_manquantes`, `n_inattendues`,
`taux_conformite_global`, `pieces`).

**Note sur les dépendances lourdes** : `torch`/`opencv`/`segmentation-models-pytorch`/`PyMuPDF`
ne sont importés que lorsqu'une inspection réelle tourne (import différé dans
`RealAIService.analyze()`). Le mode mock (`AI_ENABLED=false`, par défaut)
n'en a jamais besoin.

## 11. Tests

```bash
pytest tests/ -v
```

Couvre : démarrage de l'app, `/health`, `/camera/status`, `/camera/capture`,
`/ai/status`, `/inspection/run` (mode mock), validité des schémas Pydantic,
et la détection des checkpoints disponibles par `ModelManager` en mode réel.

## 12. CORS

Origines autorisées définies via `CORS_ORIGINS` dans `.env`
(`http://localhost:3000,http://localhost:5173` par défaut — couvre CRA et
Vite).
