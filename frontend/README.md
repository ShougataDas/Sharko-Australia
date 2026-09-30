# Sharko website

The public website of [Sharko](../README.md): a short video story about how sharks hunt and
move, then an interactive map of predicted shark areas around Australia.

**Live:** https://sharko-omega.vercel.app/ (Vercel)

## What's on the site

| Part | What it does | Code |
|---|---|---|
| Story | Six full-screen video chapters on shark hunting, navigation and their role in the ocean, with GSAP text animations | `src/components/VideoHero*.tsx` |
| Prediction map | Mapbox satellite map. Pick a date and a species (tiger, bull, great white) to see predicted **presence areas** (red) and **habitat areas** (green) as polygons from the API | `src/components/Mapbox.tsx` |
| AI assistant | Chat panel that answers questions about sharks and the project | `src/components/AIAssistant.tsx` |
| Tag concept (`/tag`) | Animated diagram of the proposed shark tag and how its data travels: underwater processing → surface transmission → satellite relay → users | `src/components/Sensor.tsx`, `DataFlow.tsx`, `TagDiagram.tsx` |

## Services it calls

| Service | URL | Used for |
|---|---|---|
| Sharko API | `https://midul914-sharko-api.hf.space` ([code](../api/)) | `/predict/presence`, `/predict/habitat` |
| RAG assistant | `https://midul914-sharo-rag-agent.hf.space/ask` | AI assistant answers |
| Mapbox | via `VITE_MAPBOX_TOKEN` | base map |

The API URLs are set in `src/components/Mapbox.tsx` and `src/components/AIAssistant.tsx`. To use a
local API, change them to `http://localhost:8000`.

## Run locally

Requires Node 18+.

```bash
cd frontend
npm install
cp .env.example .env        # then put your Mapbox public token in .env
npm run dev                 # http://localhost:5173
```

Production build: `npm run build` (output in `dist/`).

## Tech stack

React 18 + TypeScript, Vite 5, Tailwind CSS 4, React Router, Mapbox GL, GSAP, Turf.js.

## Project files

- `public/sharks.json` - the species shown in the map selector, with descriptions
- `src/assets/` - chapter videos (compressed) and images
- `src/store/heroStore.ts` - which story chapter is showing
- `PROJECT_DESCRIPTION.txt` - detailed technical description of every component

The original uncompressed videos (`src/assets/compressed.zip`, 39 MB) are not included; the
site uses the compressed `*.mp4` files.
