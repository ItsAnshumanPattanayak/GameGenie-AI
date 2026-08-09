# GameGenie AI

A complete React 18 + TypeScript + Vite frontend for AI-assisted game discovery, recommendation, generation, and play. It includes an offline mock-data fallback and a configurable Phaser Space Shooter.

## Run locally

```bash
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Build

```bash
npm run build
npm run preview
```

## Optional backend

Copy `.env.example` to `.env.local` and set `VITE_API_BASE_URL`. The frontend calls:

- `POST /api/search/interpret`
- `POST /api/search/recommend`
- `POST /api/generator/generate`

When the backend is unavailable, the app automatically uses local data and generation logic.
