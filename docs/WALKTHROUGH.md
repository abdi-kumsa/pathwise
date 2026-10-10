# Walkthrough script (recording)

This is the click script for the video still owed. We cannot record it in this
environment. No Playwright / browser MCP here (same as Wave 7). The live
substitute is `pytest tests/test_honesty_live.py tests/test_scopes.py` plus
`cd frontend && npm test`.

Stack: frontend `http://localhost:3001`, API `http://localhost:8000`.
Password for every demo user: **`pathwise123`**.

Before recording: `docker compose up` until `/health` reports all models `true`.
Confirm the provenance chip is in the shell (top bar).

---

## 1. Student (`student`)

1. Open `/login`. Click the student account (or type `student` / `pathwise123`).
2. Land on **Profile & eligibility**. Point at the provenance chip. Point at
   the simulated DataNote. Show the signed-in name is `student`.
3. Open **Labour outlook**. If occupations are withheld, read the cell-size
   caveat (n < 5).
4. Open **Alternative paths**. Show the ranking note: fit classification is
   not used; weights and method are visible.
5. Do **not** open leftover US career / placement / salary pages from the
   sidebar — they are hidden from nav. Skip them unless showing a bookmark.
6. Sign out.

## 2. University (`university`)

1. Sign in as `university`. Land on **Overview** (Addis Ababa University).
2. Open **Programme health**. Show expand / maintain / review — not fit class.
3. Open **Unconstrained demand**, then **Constrained enrolment**. Say the
   constraint layer is exam, quota, priority, capacity. Skip leftover US
   enrolment LSTM (hidden from nav).
4. Do **not** paste `?institution=Hawassa University` on camera except to
   show the 403 if you want the RBAC beat — prefer skipping live 403s.
5. Sign out.

## 3. MoE (`moe`)

1. Sign in as `moe`. Land on **National snapshot**. Provenance chip still
   simulated.
2. Open **Policy simulator**. Change one control. Click **Persist unofficial
   scenario**. Read `official_forecast: false` from the confirmation.
3. Open **Field priority**. Show factor columns (labour shortage, national
   priority, student demand, feasibility). Say what-if is not circular.
4. Optionally skip leftover US field explorer (hidden from nav).
5. Sign out.

## 4. MoL (`mol`)

1. Sign in as `mol`. Land on **Labour pulse**.
2. Open **Sector forecast**. Simulated note.
3. Open **Workforce report**. Download CSV or PDF. Say the download writes a
   `report_export` audit row and is not an official circular.
4. Open **Skills heatmap**. Show the caveat: fit class is not a ranking.
5. Sign out.

## 5. Admin (`admin`)

1. Sign in as `admin`. Land on **Overview**.
2. Open **Data pipeline**. Count **20** feeds. Four families: education,
   labor, policy, investment.
3. Open **Importance & AHP**.
   - Panel 1: learned importance (SHAP / permutation).
   - Panel 2: collection-priority tiers. Say they are not blended.
4. Submit an inconsistent AHP matrix (CR > 0.1). Show **422** / `weights: null`.
5. Open **Accounts**. Show the users table. Mention GET `/api/users` returns
   `{ n, rows }` so provenance middleware stamps the object.
6. Optionally open **Audit log**, filter `report_export` from the MoL step.

---

## Outro (10 seconds)

- Ethiopia-only on the request path.
- Rank on real signal; fit classification is not a ranking.
- SHAP and AHP stay separate.
- Simulated until official files replace the parquets.
- Demo password is not a production secret.
