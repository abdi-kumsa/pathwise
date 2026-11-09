# PathWise

PathWise is a **five-role** education–employment alignment platform for Ethiopia.
It forecasts student demand (Model 1), labour demand (Model 2) and the gap
between them (Model 3), then shows each audience only the pages it may see.

Figures are **simulated Ethiopian structure, 2016–2025**, not official MoE,
MoLS or ESS statistics. See [docs/DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md).

| Sign in as | Role | Lands on |
|---|---|---|
| `student` | Student | Profile & eligibility |
| `university` | University (Addis Ababa University) | Institution overview |
| `moe` | Ministry of Education | National snapshot |
| `mol` | Ministry of Labour | Labour pulse |
| `admin` | Administrator | Platform overview |

Demo password: **`pathwise123`**. Frontend `http://localhost:3001`, API `http://localhost:8000`.

The leftover US placement / salary / LSTM / Prophet tools are **off by default**.
They are not Ethiopia Model 1 or 2, and the 2026-11-07 audit found each loses to
a trivial baseline. Set `LEGACY_US_MODELS=1` (and `VITE_LEGACY_US_MODELS=true`,
plus `--build-arg LEGACY_US_MODELS=1` for the image) to bring them back.

---

## Repository

```
pathwise/
├── backend/      FastAPI — Models 1–3, five role APIs, admin, AHP
├── frontend/     React + Vite — five role dashboards
├── ml/           Ethiopia M1/M2/M3, AHP, leftover US artefacts
├── data/ethiopia 20 fact tables + reference dimensions
├── docs/         Spec, provenance, user guide, methodology
└── docker-compose.yml
```

- [docs/USER_GUIDE.md](docs/USER_GUIDE.md) — five role walkthroughs
- [docs/TECHNICAL.md](docs/TECHNICAL.md) — ports, routers, tests
- [docs/METHODOLOGY.md](docs/METHODOLOGY.md) — DOC1 steps 1–7
- [docs/WALKTHROUGH.md](docs/WALKTHROUGH.md) — recording script
- [docs/audit/](docs/audit/) — 2026-11-07 audit and phased improvement plan

## Quick start

```bash
cp .env.example .env
docker compose up
```

Host ports: `FRONTEND_HOST_PORT` (3001), `API_HOST_PORT` (8000), `DB_HOST_PORT` (5434).

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI |
| Auth / governance | PostgreSQL (`users`, audit, scenarios, AHP, expert validations) |
| Dashboards | Ethiopia parquets under `data/ethiopia/` |
| Models | Four-candidate rolling-origin backtest per target, best per horizon (M1/M2); cohort-lagged supply and coverage-based gaps (M3); AHP separate |
| Frontend | React + Vite + Recharts |
| Tests | pytest (unit / `live` markers) + Vitest; GitHub Actions CI |
