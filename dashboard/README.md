# Inspection Control Center — Frontend

Dashboard React pour le système de contrôle de conformité des tracés (SARTEX).
Consomme l'API FastAPI (`api/`) qui exécute le pipeline U-Net réel ; peut
aussi tourner en données mockées, sans backend, pour le développement UI.

## Lancer le projet

```bash
npm install
npm run dev
```

## Structure

```
src/
├── components/
│   ├── layout/         Sidebar, Header, AppLayout
│   ├── inspection/      TraceeSelector, ConformitySummary, PieceVerdictTable
│   ├── analytics/       StatCard, ConfidenceTrendChart, DurationTrendChart
│   └── ui/               Card, Badge, ProgressBar (design system primitives)
├── pages/               Dashboard, Inspection, History, Analytics, Settings
├── hooks/               useInspectionData (stats/history), useLiveClock
├── services/             inspectionService.js (API layer), mockData.js
├── context/              InspectionContext.jsx (état d'inspection partagé)
└── styles/               tokens.css (design tokens), global.css
```

> Historique : les premières itérations du dashboard avaient une structure
> `camera/` + `phases/` (positionnement caméra générique, avant la bascule
> vers le vrai workflow de conformité tracé → verdict par pièce). Cette
> structure a été remplacée par `inspection/` ci-dessus ; ce README a été
> mis à jour en conséquence.

## Design system

Tokens définis dans `src/styles/tokens.css` et exposés à Tailwind dans `tailwind.config.js`
(`bg`, `surface`, `sunken`, `border`, `ink`, `muted`, `accent`, `success`, `warning`, `error`,
chacun avec une variante `-soft`). Typo : IBM Plex Sans (UI) + IBM Plex Mono (lectures chiffrées :
confiance, temps, session ID, ID d'historique).

## Bascule mock / backend réel

Tout passe par **`src/services/inspectionService.js`** (voir `.env.example`) :
- `VITE_USE_MOCK=true` (ou `VITE_API_BASE_URL` absent) → l'app utilise `mockData.js`,
  sans dépendance au backend. Utile pour développer l'UI seule.
- `VITE_USE_MOCK=false` + `VITE_API_BASE_URL` pointant vers l'API (`http://localhost:8000/api/v1`
  par défaut) → appels réels vers FastAPI (`api/`).
- Aucun composant ne dépend de la source des données — ils consomment uniquement les hooks
  (`useInspectionData`) et les fonctions de `inspectionService.js`, donc rien d'autre à changer.

Forme JSON réellement retournée par `POST /api/v1/inspection/run` en mode réel
(voir `api/app/schemas/inspection.py`, reproduite par `mockData.js`) :

```json
{
  "inspection_id": "INS-2026-4F3A1C",
  "status": "completed",
  "result": "PASS",
  "confidence": 96.4,
  "defects": [],
  "processing_time_ms": 842,
  "created_at": "2026-09-16T10:12:00+00:00",
  "tracee": "Tracee1",
  "code_modele": "T1-JUPE-01",
  "n_pieces_reference": 25,
  "n_conformes": 24,
  "n_non_conformes": 1,
  "n_manquantes": 0,
  "n_inattendues": 0,
  "taux_conformite_global": 96.0,
  "pieces": [
    {
      "piece_reference": "DEVANT",
      "largeur_attendue_cm": 42.0,
      "hauteur_attendue_cm": 68.5,
      "largeur_mesuree_cm": 42.3,
      "hauteur_mesuree_cm": 68.6,
      "erreur_cm": 0.3,
      "verdict": "CONFORME"
    }
  ]
}
```
