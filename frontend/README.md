# SIH 2026 — Marine Incident Intelligence

Frontend foundation for an AI-assisted oil spill detection and incident-intelligence platform. It is decision support: Oil Spill Candidates and Vessels of Interest require analyst or field verification.

## Install and run

```bash
npm install
npm run dev
```

For a production check:

```bash
npm run build
```

## Structure

`src/components` holds reusable UI modules, grouped by layout, map, incidents, evidence, vessels, analytics, and common elements. `src/pages` contains routed screens. `src/data` contains local fixtures only. `src/services` defines the data boundary, `src/hooks` consumes that boundary, and `src/utils` holds reusable helpers.

## Mock data

Components never import fixture files directly. They call hooks such as `useIncidents`, which use the `api` contract in `src/services/api.js`. During this frontend-only phase, that contract delegates to `mockApi.js`, which returns asynchronous copies of the local fixture data.

## Future FastAPI integration

Set `VITE_API_BASE_URL` in a local `.env` file (see `.env.example`). When FastAPI is available, replace the four delegates in `src/services/api.js` with calls through the exported Axios `http` instance—preserving the existing method names and response shapes. Pages and components will not need to be rewritten.
