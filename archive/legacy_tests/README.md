# Legacy test scripts

Script-style suites from the US-dataset era. None of them defines a pytest test:
each runs its checks at import time and prints `[PASS]`/`[FAIL]`.

- `test_phase4.py`, `test_phase5.py`, `test_integration_docker.py` call the
  retired market and enrollment endpoints, two of them on the old port 8080.
- `test_xgboost.py`, `test_shap.py`, `test_lstm.py`, `test_prophet.py` load the
  US placement, LSTM and Prophet artefacts directly. Under pytest they ran
  during collection (loading TensorFlow on every run) and reported nothing.

Run any of them by hand from the project root, e.g. `python archive/legacy_tests/test_xgboost.py`. They are kept for reference, not collected by pytest
(`pytest.ini` sets `testpaths = tests`).

Those endpoints now exist only when the API runs with `LEGACY_US_MODELS=1`
(waiver WV.US1). Their behaviour is covered by the `@legacy` classes in
`backend/tests/test_api.py`, which run automatically when that flag is on.

Moved here in Phase 1 of the 2026-11-07 improvement plan
(`docs/audit/2026-11-07-improvement-plan.md`).
