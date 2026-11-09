"""
Phase 7 — Offline Unit Test Suite
Tests ml/monitor_models.py and ml/retrain_all.py in full isolation.

Every file-system touch, ML-library call, and subprocess spawn is mocked so
the suite runs without Docker, Postgres, or any trained model files.

Sections:
  1  monitor_models — path resolution & constants
  2  monitor_models — _load_model()
  3  monitor_models — _load_baseline()
  4  monitor_models — _load_recent_records()
  5  monitor_models — run_monitor() happy path (no drift)
  6  monitor_models — run_monitor() drift detected
  7  monitor_models — run_monitor() missing model files
  8  monitor_models — run_monitor() missing parquet
  9  monitor_models — run_monitor() ROC-AUC single-class guard
  10 retrain_all    — STEPS list integrity
  11 retrain_all    — run_step() success
  12 retrain_all    — run_step() failure raises RuntimeError
  13 retrain_all    — main() all steps succeed → exit 0
  14 retrain_all    — main() one step fails → exit 1 with name
  15 retrain_all    — main() first step fails → remaining steps not run
  16 test_api.py    — file structure and import checks
  17 test_api.py    — fixture and constant definitions
  18 test_api.py    — test class and method presence
  19 Cross-cutting  — no hard-coded paths survive across modules
  20 Cross-cutting  — exit-code contract

Run (from project root):
    python -m pytest tests/test_phase7.py -v
"""

import ast
import importlib.util
import json
import os
import sys
import unittest
import unittest.mock as mock
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# ── Project root ──────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
ML_DIR       = PROJECT_ROOT / "ml"
TESTS_DIR    = PROJECT_ROOT / "tests"
BACKEND_TESTS_DIR = PROJECT_ROOT / "backend" / "tests"

MONITOR_PY   = ML_DIR / "monitor_models.py"
RETRAIN_PY   = ML_DIR / "retrain_all.py"
API_TEST_PY  = BACKEND_TESTS_DIR / "test_api.py"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_source(path: Path, module_name: str, extra_mocks: dict = None):
    """
    Import a source file with heavy dependencies pre-stubbed.
    extra_mocks: {dotted.module.name: mock_object} applied before import.
    """
    stubs = {
        "numpy":                      MagicMock(),
        "pandas":                     MagicMock(),
        "sklearn":                    MagicMock(),
        "sklearn.metrics":            MagicMock(),
        "sklearn.metrics.accuracy_score": MagicMock(return_value=0.88),
        "sklearn.metrics.f1_score":       MagicMock(return_value=0.93),
        "sklearn.metrics.roc_auc_score":  MagicMock(return_value=0.95),
        "xgboost":                    MagicMock(),
        "tensorflow":                 MagicMock(),
        "httpx":                      MagicMock(),
        "pytest":                     MagicMock(),
    }
    if extra_mocks:
        stubs.update(extra_mocks)

    with mock.patch.dict(sys.modules, stubs):
        spec   = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


def _ast_source(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _function_names(tree: ast.Module) -> set:
    return {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}


def _class_names(tree: ast.Module) -> set:
    return {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}


def _imports(tree: ast.Module) -> set:
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module.split(".")[0])
    return names


def _string_literals(tree: ast.Module) -> list:
    return [n.s for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.s, str)]


# =============================================================================
# Section 1 — monitor_models: path resolution & constants
# =============================================================================

class TestMonitorConstants(unittest.TestCase):

    def setUp(self):
        import numpy as np
        import pandas as pd
        self._np = np
        self._pd = pd
        self.tree = _ast_source(MONITOR_PY)

    def test_file_exists(self):
        self.assertTrue(MONITOR_PY.exists(), f"Missing: {MONITOR_PY}")

    def test_drift_threshold_defined(self):
        """DRIFT_THRESHOLD must be a module-level constant."""
        assigns = {
            n.targets[0].id: n.value
            for n in ast.walk(self.tree)
            if isinstance(n, ast.Assign)
            and len(n.targets) == 1
            and isinstance(n.targets[0], ast.Name)
        }
        self.assertIn("DRIFT_THRESHOLD", assigns)

    def test_sample_size_defined(self):
        assigns = {
            n.targets[0].id: n.value
            for n in ast.walk(self.tree)
            if isinstance(n, ast.Assign)
            and len(n.targets) == 1
            and isinstance(n.targets[0], ast.Name)
        }
        self.assertIn("SAMPLE_SIZE", assigns)

    def test_drift_threshold_value(self):
        """Threshold must be 0.10 as documented."""
        mod = _load_source(MONITOR_PY, "monitor_models_c1")
        self.assertAlmostEqual(mod.DRIFT_THRESHOLD, 0.10)

    def test_sample_size_value(self):
        mod = _load_source(MONITOR_PY, "monitor_models_c2")
        self.assertEqual(mod.SAMPLE_SIZE, 50)

    def test_required_functions_present(self):
        names = _function_names(self.tree)
        for fn in ("_load_model", "_load_baseline", "_load_recent_records", "run_monitor"):
            self.assertIn(fn, names, f"Missing function: {fn}")

    def test_cron_comment_present(self):
        """The cron schedule must be documented in the source."""
        src = MONITOR_PY.read_text(encoding="utf-8")
        self.assertIn("cron", src.lower())
        self.assertIn("0 7", src)

    def test_exit_codes_documented(self):
        src = MONITOR_PY.read_text(encoding="utf-8")
        self.assertIn("Exit codes", src)


# =============================================================================
# Section 2 — monitor_models: _load_model()
# =============================================================================

class TestLoadModel(unittest.TestCase):

    def _make_module(self):
        return _load_source(MONITOR_PY, "monitor_models_lm")

    def test_load_model_opens_two_pickle_files(self):
        mod = self._make_module()
        fake_model    = MagicMock()
        fake_features = ["gpa_scaled", "internships"]

        m_open = mock.mock_open()
        pickles = [fake_model, fake_features]
        idx = {"i": 0}

        def fake_load(f):
            val = pickles[idx["i"]]
            idx["i"] += 1
            return val

        with patch("builtins.open", m_open):
            with patch("pickle.load", side_effect=fake_load):
                model, features = mod._load_model()

        self.assertEqual(model,    fake_model)
        self.assertEqual(features, fake_features)

    def test_load_model_raises_file_not_found(self):
        mod = self._make_module()
        with patch("builtins.open", side_effect=FileNotFoundError("no file")):
            with self.assertRaises(FileNotFoundError):
                mod._load_model()

    def test_load_model_uses_model_dir(self):
        """Both pickle paths must be inside MODEL_DIR."""
        self._make_module()          # must import cleanly
        src  = MONITOR_PY.read_text(encoding="utf-8")
        self.assertIn("placement_xgboost.pkl",      src)
        self.assertIn("placement_feature_names.pkl", src)


# =============================================================================
# Section 3 — monitor_models: _load_baseline()
# =============================================================================

class TestLoadBaseline(unittest.TestCase):

    def _mod(self):
        return _load_source(MONITOR_PY, "monitor_models_lb")

    def test_returns_xgboost_placement_section(self):
        mod = self._mod()
        metrics = {
            "xgboost_placement": {"accuracy": 0.88, "f1_score": 0.94},
            "other_key":         {"x": 1},
        }
        m = mock_open(read_data=json.dumps(metrics))
        with patch("builtins.open", m):
            result = mod._load_baseline()
        self.assertEqual(result["accuracy"],  0.88)
        self.assertEqual(result["f1_score"],  0.94)
        self.assertNotIn("other_key", result)

    def test_missing_metrics_file_raises(self):
        mod = self._mod()
        with patch("builtins.open", side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                mod._load_baseline()

    def test_missing_key_returns_empty_dict(self):
        mod = self._mod()
        m = mock_open(read_data=json.dumps({"other": {}}))
        with patch("builtins.open", m):
            result = mod._load_baseline()
        self.assertEqual(result, {})


# =============================================================================
# Section 4 — monitor_models: _load_recent_records()
# =============================================================================

class TestLoadRecentRecords(unittest.TestCase):

    def _mod(self):
        return _load_source(MONITOR_PY, "monitor_models_lr")

    def test_sorts_by_enrollment_year_descending(self):
        import pandas as pd
        mod = self._mod()

        df = pd.DataFrame({
            "gpa_scaled":      [0.9, 0.7, 0.8],
            "internships":     [3, 1, 2],
            "enrollment_year": [2022, 2024, 2023],
            "placed":          [1, 0, 1],
        })

        # mod.pd is the MagicMock bound at import; set its read_parquet return value directly
        mod.pd.read_parquet.return_value = df
        X, y = mod._load_recent_records(["gpa_scaled", "internships"])

        # After descending sort the first row should be enrollment_year=2024
        self.assertEqual(list(y.values), [0, 1, 1])   # 2024, 2023, 2022 order

    def test_returns_only_feature_columns(self):
        import pandas as pd
        mod = self._mod()

        df = pd.DataFrame({
            "gpa_scaled":      [0.9, 0.8],
            "internships":     [2, 1],
            "placed":          [1, 0],
            "extra_col":       [99, 88],
            "enrollment_year": [2024, 2023],
        })

        feature_names = ["gpa_scaled", "internships"]
        mod.pd.read_parquet.return_value = df
        X, y = mod._load_recent_records(feature_names)

        self.assertListEqual(list(X.columns), feature_names)
        self.assertNotIn("extra_col", X.columns)

    def test_missing_parquet_raises(self):
        mod = self._mod()
        mod.pd.read_parquet.side_effect = FileNotFoundError("parquet")
        with self.assertRaises(FileNotFoundError):
            mod._load_recent_records(["gpa_scaled"])


# =============================================================================
# Section 5 — monitor_models: run_monitor() happy path
# =============================================================================

class TestRunMonitorHappyPath(unittest.TestCase):

    def _make_happy_mocks(self, accuracy=0.87, f1=0.92):
        """Return (mock_model, feature_names, X, y, baseline) for a healthy run."""
        import numpy as np
        import pandas as pd

        fake_model        = MagicMock()
        feature_names     = ["gpa_scaled", "internships"]
        X                 = pd.DataFrame({"gpa_scaled": [0.8]*50, "internships": [2]*50})
        y                 = pd.Series([1]*45 + [0]*5)
        fake_model.predict.return_value        = np.array([1]*50)
        fake_model.predict_proba.return_value  = np.column_stack([[0.1]*50, [0.9]*50])
        baseline = {"accuracy": accuracy, "f1_score": f1}
        return fake_model, feature_names, X, y, baseline

    def test_returns_zero_when_no_drift(self):
        mod = _load_source(MONITOR_PY, "monitor_happy")
        fake_model, features, X, y, baseline = self._make_happy_mocks(0.87, 0.92)

        with patch.object(mod, "_load_model",          return_value=(fake_model, features)), \
             patch.object(mod, "_load_baseline",       return_value=baseline), \
             patch.object(mod, "_load_recent_records", return_value=(X, y)), \
             patch.object(mod, "accuracy_score",       return_value=0.87), \
             patch.object(mod, "f1_score",             return_value=0.92), \
             patch.object(mod, "roc_auc_score",        return_value=0.95):
            rc = mod.run_monitor()

        self.assertEqual(rc, 0)

    def test_prints_ok_on_healthy_run(self, capsys=None):
        mod = _load_source(MONITOR_PY, "monitor_happy2")
        import io
        fake_model, features, X, y, baseline = self._make_happy_mocks(0.88, 0.93)

        captured = io.StringIO()
        with patch.object(mod, "_load_model",          return_value=(fake_model, features)), \
             patch.object(mod, "_load_baseline",       return_value=baseline), \
             patch.object(mod, "_load_recent_records", return_value=(X, y)), \
             patch.object(mod, "accuracy_score",       return_value=0.88), \
             patch.object(mod, "f1_score",             return_value=0.93), \
             patch.object(mod, "roc_auc_score",        return_value=0.95), \
             patch("sys.stdout", captured):
            mod.run_monitor()

        output = captured.getvalue()
        self.assertIn("[OK]", output)

    def test_does_not_print_drift_on_healthy_run(self):
        mod = _load_source(MONITOR_PY, "monitor_happy3")
        import io
        fake_model, features, X, y, baseline = self._make_happy_mocks(0.88, 0.93)

        captured = io.StringIO()
        with patch.object(mod, "_load_model",          return_value=(fake_model, features)), \
             patch.object(mod, "_load_baseline",       return_value=baseline), \
             patch.object(mod, "_load_recent_records", return_value=(X, y)), \
             patch.object(mod, "accuracy_score",       return_value=0.88), \
             patch.object(mod, "f1_score",             return_value=0.93), \
             patch.object(mod, "roc_auc_score",        return_value=0.95), \
             patch("sys.stdout", captured):
            mod.run_monitor()

        self.assertNotIn("DRIFT", captured.getvalue())


# =============================================================================
# Section 6 — monitor_models: run_monitor() drift detected
# =============================================================================

class TestRunMonitorDrift(unittest.TestCase):

    def _mod(self):
        return _load_source(MONITOR_PY, "monitor_drift")

    def test_returns_one_on_accuracy_drift(self):
        mod = self._mod()
        import pandas as pd, numpy as np

        fake_model = MagicMock()
        features   = ["gpa_scaled", "internships"]
        X          = pd.DataFrame({"gpa_scaled": [0.5]*50, "internships": [0]*50})
        y          = pd.Series([0]*25 + [1]*25)
        fake_model.predict.return_value       = np.array([0]*50)
        fake_model.predict_proba.return_value = np.column_stack([[0.8]*50, [0.2]*50])
        baseline   = {"accuracy": 0.88, "f1_score": 0.93}

        with patch.object(mod, "_load_model",          return_value=(fake_model, features)), \
             patch.object(mod, "_load_baseline",       return_value=baseline), \
             patch.object(mod, "_load_recent_records", return_value=(X, y)), \
             patch.object(mod, "accuracy_score",       return_value=0.70), \
             patch.object(mod, "f1_score",             return_value=0.65), \
             patch.object(mod, "roc_auc_score",        return_value=0.72):
            rc = mod.run_monitor()

        self.assertEqual(rc, 1)

    def test_returns_one_on_f1_drift_only(self):
        mod = self._mod()
        import pandas as pd, numpy as np

        fake_model = MagicMock()
        features   = ["gpa_scaled"]
        X          = pd.DataFrame({"gpa_scaled": [0.8]*50})
        y          = pd.Series([1]*40 + [0]*10)
        fake_model.predict.return_value       = np.array([1]*50)
        fake_model.predict_proba.return_value = np.column_stack([[0.2]*50, [0.8]*50])
        # accuracy is fine but f1 dropped 12 pp
        baseline   = {"accuracy": 0.88, "f1_score": 0.95}

        with patch.object(mod, "_load_model",          return_value=(fake_model, features)), \
             patch.object(mod, "_load_baseline",       return_value=baseline), \
             patch.object(mod, "_load_recent_records", return_value=(X, y)), \
             patch.object(mod, "accuracy_score",       return_value=0.87), \
             patch.object(mod, "f1_score",             return_value=0.83), \
             patch.object(mod, "roc_auc_score",        return_value=0.90):
            rc = mod.run_monitor()

        self.assertEqual(rc, 1)

    def test_drift_message_printed(self):
        mod = self._mod()
        import pandas as pd, numpy as np, io

        fake_model = MagicMock()
        features   = ["gpa_scaled"]
        X          = pd.DataFrame({"gpa_scaled": [0.5]*50})
        y          = pd.Series([0]*30 + [1]*20)
        fake_model.predict.return_value       = np.array([0]*50)
        fake_model.predict_proba.return_value = np.column_stack([[0.9]*50, [0.1]*50])
        baseline   = {"accuracy": 0.88, "f1_score": 0.93}

        captured = io.StringIO()
        with patch.object(mod, "_load_model",          return_value=(fake_model, features)), \
             patch.object(mod, "_load_baseline",       return_value=baseline), \
             patch.object(mod, "_load_recent_records", return_value=(X, y)), \
             patch.object(mod, "accuracy_score",       return_value=0.55), \
             patch.object(mod, "f1_score",             return_value=0.50), \
             patch.object(mod, "roc_auc_score",        return_value=0.60), \
             patch("sys.stdout", captured):
            mod.run_monitor()

        self.assertIn("DRIFT", captured.getvalue())

    def test_exact_threshold_is_not_flagged(self):
        """A drop of exactly 10 pp should NOT trigger drift (threshold is >10 pp)."""
        mod = self._mod()
        import pandas as pd, numpy as np

        fake_model = MagicMock()
        features   = ["gpa_scaled"]
        X          = pd.DataFrame({"gpa_scaled": [0.8]*50})
        y          = pd.Series([1]*50)
        fake_model.predict.return_value       = np.array([1]*50)
        fake_model.predict_proba.return_value = np.column_stack([[0.1]*50, [0.9]*50])
        baseline   = {"accuracy": 0.88, "f1_score": 0.93}

        with patch.object(mod, "_load_model",          return_value=(fake_model, features)), \
             patch.object(mod, "_load_baseline",       return_value=baseline), \
             patch.object(mod, "_load_recent_records", return_value=(X, y)), \
             patch.object(mod, "accuracy_score",       return_value=0.78), \
             patch.object(mod, "f1_score",             return_value=0.93), \
             patch.object(mod, "roc_auc_score",        return_value=0.92):
            rc = mod.run_monitor()

        self.assertEqual(rc, 0)


# =============================================================================
# Section 7 — monitor_models: run_monitor() missing model files
# =============================================================================

class TestRunMonitorMissingModel(unittest.TestCase):

    def test_returns_one_when_model_pkl_missing(self):
        mod = _load_source(MONITOR_PY, "monitor_missing_model")
        with patch.object(mod, "_load_model", side_effect=FileNotFoundError("no pkl")):
            rc = mod.run_monitor()
        self.assertEqual(rc, 1)

    def test_returns_one_when_metrics_json_missing(self):
        mod = _load_source(MONITOR_PY, "monitor_missing_metrics")
        fake_model = MagicMock()
        features   = ["gpa_scaled"]
        with patch.object(mod, "_load_model",    return_value=(fake_model, features)), \
             patch.object(mod, "_load_baseline", side_effect=FileNotFoundError("no json")):
            rc = mod.run_monitor()
        self.assertEqual(rc, 1)

    def test_prints_error_message_on_missing_model(self):
        import io
        mod = _load_source(MONITOR_PY, "monitor_missing_msg")
        captured = io.StringIO()
        with patch.object(mod, "_load_model", side_effect=FileNotFoundError("missing")), \
             patch("sys.stdout", captured):
            mod.run_monitor()
        self.assertIn("ERROR", captured.getvalue())


# =============================================================================
# Section 8 — monitor_models: run_monitor() missing parquet
# =============================================================================

class TestRunMonitorMissingParquet(unittest.TestCase):

    def test_returns_one_when_parquet_missing(self):
        mod = _load_source(MONITOR_PY, "monitor_missing_parquet")
        fake_model = MagicMock()
        features   = ["gpa_scaled"]
        baseline   = {"accuracy": 0.88, "f1_score": 0.93}
        with patch.object(mod, "_load_model",          return_value=(fake_model, features)), \
             patch.object(mod, "_load_baseline",       return_value=baseline), \
             patch.object(mod, "_load_recent_records", side_effect=FileNotFoundError("parquet")):
            rc = mod.run_monitor()
        self.assertEqual(rc, 1)


# =============================================================================
# Section 9 — monitor_models: ROC-AUC single-class guard
# =============================================================================

class TestRocAucGuard(unittest.TestCase):

    def test_single_class_does_not_crash(self):
        """If all records have the same label, roc_auc_score must be skipped."""
        mod = _load_source(MONITOR_PY, "monitor_rocauc")
        import pandas as pd, numpy as np

        fake_model = MagicMock()
        features   = ["gpa_scaled"]
        X          = pd.DataFrame({"gpa_scaled": [0.9]*50})
        y          = pd.Series([1]*50)          # single class
        fake_model.predict.return_value       = np.array([1]*50)
        fake_model.predict_proba.return_value = np.column_stack([[0.1]*50, [0.9]*50])
        baseline   = {"accuracy": 0.88, "f1_score": 0.93}

        with patch.object(mod, "_load_model",          return_value=(fake_model, features)), \
             patch.object(mod, "_load_baseline",       return_value=baseline), \
             patch.object(mod, "_load_recent_records", return_value=(X, y)), \
             patch.object(mod, "accuracy_score",       return_value=1.0), \
             patch.object(mod, "f1_score",             return_value=1.0):
            try:
                rc = mod.run_monitor()
            except Exception as exc:
                self.fail(f"run_monitor() crashed on single-class data: {exc}")

        self.assertEqual(rc, 0)


# =============================================================================
# Section 10 — retrain_all: STEPS list integrity
# =============================================================================

class TestRetrainSteps(unittest.TestCase):

    def _mod(self):
        return _load_source(RETRAIN_PY, "retrain_steps")

    def test_steps_list_matches_pipeline(self):
        # Six steps since the salary model joined the pipeline: features, four
        # trainers, then the metrics refresh. Asserted against the script's own
        # list so a seventh step fails with a readable diff, not a bare count.
        mod = self._mod()
        self.assertEqual([s for s, _ in mod.STEPS], [
            "feature_engineering.py", "train_xgboost.py", "train_salary_xgboost.py",
            "train_lstm.py", "train_prophet.py", "generate_model_metrics.py",
        ])

    def test_steps_are_tuples(self):
        mod = self._mod()
        for item in mod.STEPS:
            self.assertIsInstance(item, tuple)
            self.assertEqual(len(item), 2)

    def test_expected_scripts_present(self):
        mod = self._mod()
        scripts = [s for s, _ in mod.STEPS]
        self.assertIn("feature_engineering.py",    scripts)
        self.assertIn("train_xgboost.py",           scripts)
        self.assertIn("train_lstm.py",              scripts)
        self.assertIn("train_prophet.py",           scripts)
        self.assertIn("generate_model_metrics.py",  scripts)

    def test_feature_engineering_runs_first(self):
        mod = self._mod()
        self.assertEqual(mod.STEPS[0][0], "feature_engineering.py")

    def test_generate_metrics_runs_last(self):
        mod = self._mod()
        self.assertEqual(mod.STEPS[-1][0], "generate_model_metrics.py")

    def test_xgboost_before_lstm(self):
        mod  = self._mod()
        names = [s for s, _ in mod.STEPS]
        self.assertLess(names.index("train_xgboost.py"), names.index("train_lstm.py"))

    def test_descriptions_are_non_empty_strings(self):
        mod = self._mod()
        for _, desc in mod.STEPS:
            self.assertIsInstance(desc, str)
            self.assertGreater(len(desc.strip()), 0)


# =============================================================================
# Section 11 — retrain_all: run_step() success
# =============================================================================

class TestRunStepSuccess(unittest.TestCase):

    def _mod(self):
        return _load_source(RETRAIN_PY, "retrain_run_step")

    def test_run_step_calls_subprocess_run(self):
        mod = self._mod()
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_sub:
            mod.run_step(1, "train_xgboost.py", "Train XGBoost")

        mock_sub.assert_called_once()

    def test_run_step_passes_python_executable(self):
        mod = self._mod()
        mock_result = MagicMock(returncode=0)

        with patch("subprocess.run", return_value=mock_result) as mock_sub:
            mod.run_step(1, "train_xgboost.py", "Train XGBoost")

        args = mock_sub.call_args[0][0]
        self.assertEqual(args[0], sys.executable)

    def test_run_step_no_exception_on_success(self):
        mod = self._mod()
        mock_result = MagicMock(returncode=0)

        with patch("subprocess.run", return_value=mock_result):
            try:
                mod.run_step(2, "train_lstm.py", "Train LSTM")
            except Exception as exc:
                self.fail(f"run_step raised unexpectedly: {exc}")

    def test_run_step_prints_step_label(self):
        import io
        mod = self._mod()
        mock_result = MagicMock(returncode=0)
        captured = io.StringIO()

        with patch("subprocess.run", return_value=mock_result), \
             patch("sys.stdout", captured):
            mod.run_step(3, "train_prophet.py", "Train Prophet")

        self.assertIn("[3/", captured.getvalue())


# =============================================================================
# Section 12 — retrain_all: run_step() failure raises RuntimeError
# =============================================================================

class TestRunStepFailure(unittest.TestCase):

    def _mod(self):
        return _load_source(RETRAIN_PY, "retrain_fail")

    def test_non_zero_exit_raises_runtime_error(self):
        mod = self._mod()
        mock_result = MagicMock(returncode=1)

        with patch("subprocess.run", return_value=mock_result):
            with self.assertRaises(RuntimeError):
                mod.run_step(2, "train_lstm.py", "Train LSTM")

    def test_runtime_error_message_contains_script_name(self):
        mod = self._mod()
        mock_result = MagicMock(returncode=2)

        with patch("subprocess.run", return_value=mock_result):
            with self.assertRaises(RuntimeError) as ctx:
                mod.run_step(3, "train_prophet.py", "Train Prophet")

        self.assertIn("train_prophet.py", str(ctx.exception))

    def test_runtime_error_contains_exit_code(self):
        mod = self._mod()
        mock_result = MagicMock(returncode=99)

        with patch("subprocess.run", return_value=mock_result):
            with self.assertRaises(RuntimeError) as ctx:
                mod.run_step(1, "feature_engineering.py", "Rebuild parquet")

        self.assertIn("99", str(ctx.exception))


# =============================================================================
# Section 13 — retrain_all: main() all steps succeed → exit 0
# =============================================================================

class TestRetrainMainSuccess(unittest.TestCase):

    def test_main_returns_zero_when_all_pass(self):
        mod = _load_source(RETRAIN_PY, "retrain_main_ok")
        mock_result = MagicMock(returncode=0)

        with patch("subprocess.run", return_value=mock_result):
            rc = mod.main()

        self.assertEqual(rc, 0)

    def test_main_runs_every_step_once(self):
        mod = _load_source(RETRAIN_PY, "retrain_main_all")
        mock_result = MagicMock(returncode=0)

        with patch("subprocess.run", return_value=mock_result) as mock_sub:
            mod.main()

        self.assertEqual(mock_sub.call_count, len(mod.STEPS))

    def test_main_prints_complete_message(self):
        import io
        mod = _load_source(RETRAIN_PY, "retrain_main_msg")
        mock_result = MagicMock(returncode=0)
        captured = io.StringIO()

        with patch("subprocess.run", return_value=mock_result), \
             patch("sys.stdout", captured):
            mod.main()

        out = captured.getvalue().lower()
        self.assertTrue("complete" in out or "done" in out or "retrain" in out)


# =============================================================================
# Section 14 — retrain_all: main() one step fails → exit 1
# =============================================================================

class TestRetrainMainFailure(unittest.TestCase):

    def test_main_returns_one_on_step_failure(self):
        mod = _load_source(RETRAIN_PY, "retrain_main_fail")
        fail_result = MagicMock(returncode=1)

        with patch("subprocess.run", return_value=fail_result):
            rc = mod.main()

        self.assertEqual(rc, 1)

    def test_main_prints_failed_message(self):
        import io
        mod = _load_source(RETRAIN_PY, "retrain_main_fail_msg")
        fail_result = MagicMock(returncode=1)
        captured = io.StringIO()

        with patch("subprocess.run", return_value=fail_result), \
             patch("sys.stdout", captured):
            mod.main()

        self.assertIn("FAILED", captured.getvalue())


# =============================================================================
# Section 15 — retrain_all: first step fails → remaining steps not run
# =============================================================================

class TestRetrainEarlyExit(unittest.TestCase):

    def test_stops_after_first_failure(self):
        mod = _load_source(RETRAIN_PY, "retrain_early_exit")

        call_count = {"n": 0}
        def counting_run(*args, **kwargs):
            call_count["n"] += 1
            return MagicMock(returncode=1)   # always fail

        with patch("subprocess.run", side_effect=counting_run):
            mod.main()

        # Only 1 subprocess.run should have been called — the failing step
        self.assertEqual(call_count["n"], 1)

    def test_second_step_skipped_if_first_fails(self):
        mod = _load_source(RETRAIN_PY, "retrain_skip")

        called_scripts = []
        def track_run(cmd, *args, **kwargs):
            called_scripts.append(os.path.basename(cmd[1]))
            return MagicMock(returncode=1)

        with patch("subprocess.run", side_effect=track_run):
            mod.main()

        self.assertEqual(len(called_scripts), 1)
        self.assertEqual(called_scripts[0], "feature_engineering.py")


# =============================================================================
# Section 16 — test_api.py: file structure and import checks
# =============================================================================

class TestApiFileStructure(unittest.TestCase):

    def setUp(self):
        self.assertTrue(API_TEST_PY.exists(), f"Missing: {API_TEST_PY}")
        self.tree = _ast_source(API_TEST_PY)

    def test_imports_pytest(self):
        imports = _imports(self.tree)
        self.assertIn("pytest", imports)

    def test_imports_httpx(self):
        imports = _imports(self.tree)
        self.assertIn("httpx", imports)

    def test_imports_os(self):
        imports = _imports(self.tree)
        self.assertIn("os", imports)

    def test_base_url_env_var_used(self):
        src = API_TEST_PY.read_text(encoding="utf-8")
        self.assertIn("BASE_URL",   src)
        self.assertIn("os.getenv",  src)


# =============================================================================
# Section 17 — test_api.py: fixture and constant definitions
# =============================================================================

class TestApiFixtures(unittest.TestCase):

    def setUp(self):
        self.tree = _ast_source(API_TEST_PY)
        self.src  = API_TEST_PY.read_text(encoding="utf-8")

    def test_client_fixture_defined(self):
        fns = _function_names(self.tree)
        self.assertIn("client", fns)

    def test_strong_student_fixture_defined(self):
        self.assertIn("STRONG_STUDENT", self.src)

    def test_weak_student_fixture_defined(self):
        self.assertIn("WEAK_STUDENT", self.src)

    def test_known_programs_constant_defined(self):
        self.assertIn("KNOWN_PROGRAMS", self.src)

    def test_strong_student_has_all_required_fields(self):
        self.assertIn('"gpa"',                self.src)
        self.assertIn('"internships"',         self.src)
        self.assertIn('"projects"',            self.src)
        self.assertIn('"communication_score"', self.src)
        self.assertIn('"program"',             self.src)

    def test_known_programs_contains_12_entries(self):
        # Parse KNOWN_PROGRAMS set literal from AST
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == "KNOWN_PROGRAMS":
                        if isinstance(node.value, ast.Set):
                            self.assertEqual(len(node.value.elts), 12)
                            return
        # If not a set literal, count by searching the src
        programs = [
            "BS Computer Science", "BS Data Science", "Certificate Data Analytics",
            "MBA Product Management", "MS Artificial Intelligence", "MS Business Analytics",
            "MS Cloud Computing", "MS Computer Science", "MS Cybersecurity",
            "MS Data Science", "MS Human-Computer Interaction", "MS Information Technology",
        ]
        for prog in programs:
            self.assertIn(prog, self.src, f"Missing program: {prog}")

    def test_session_scope_on_client_fixture(self):
        self.assertIn('scope="session"', self.src)


# =============================================================================
# Section 18 — test_api.py: test class and method presence
# =============================================================================

class TestApiTestClasses(unittest.TestCase):

    def setUp(self):
        self.tree = _ast_source(API_TEST_PY)
        self.classes = _class_names(self.tree)
        self.fns     = _function_names(self.tree)

    def test_test_health_class_present(self):
        self.assertIn("TestHealth", self.classes)

    def test_test_market_overview_class_present(self):
        self.assertIn("TestMarketOverview", self.classes)

    def test_test_top_companies_class_present(self):
        self.assertIn("TestTopCompanies", self.classes)

    def test_test_demand_forecast_class_present(self):
        self.assertIn("TestDemandForecast", self.classes)

    def test_test_enrollment_summary_class_present(self):
        self.assertIn("TestEnrollmentSummary", self.classes)

    def test_test_enrollment_forecast_class_present(self):
        self.assertIn("TestEnrollmentForecast", self.classes)

    def test_test_predict_placement_class_present(self):
        self.assertIn("TestPredictPlacement", self.classes)

    def test_test_monitoring_class_present(self):
        self.assertIn("TestMonitoring", self.classes)

    def test_test_data_consistency_class_present(self):
        self.assertIn("TestDataConsistency", self.classes)

    def test_directional_ordering_test_present(self):
        self.assertIn("test_directional_ordering", self.fns)

    def test_error_handling_tests_present(self):
        self.assertIn("test_predict_missing_program_422", self.fns)
        self.assertIn("test_predict_invalid_gpa_422",     self.fns)

    def test_forecast_all_12_programs_test_present(self):
        self.assertIn("test_forecast_all_12_programs", self.fns)

    def test_at_least_50_test_methods_defined(self):
        test_methods = [f for f in self.fns if f.startswith("test_")]
        self.assertGreaterEqual(len(test_methods), 50,
            f"Only {len(test_methods)} test methods found — expected ≥ 50")


# =============================================================================
# Section 19 — Cross-cutting: no Windows-only hard-coded paths
# =============================================================================

class TestNoPlatformPaths(unittest.TestCase):

    def _check_no_hardcoded_path(self, path: Path):
        src = path.read_text(encoding="utf-8")
        bad_patterns = [
            "C:\\Users\\blu",
            "C:/Users/blu",
            "/home/abdi",
        ]
        for pat in bad_patterns:
            self.assertNotIn(pat, src,
                f"{path.name} contains hard-coded path: {pat!r}")

    def test_monitor_no_hardcoded_path(self):
        self._check_no_hardcoded_path(MONITOR_PY)

    def test_retrain_no_hardcoded_path(self):
        self._check_no_hardcoded_path(RETRAIN_PY)

    def test_api_test_no_hardcoded_path(self):
        self._check_no_hardcoded_path(API_TEST_PY)

    def test_monitor_uses_abspath_for_root(self):
        src = MONITOR_PY.read_text(encoding="utf-8")
        self.assertTrue(
            "os.path.abspath" in src or "__file__" in src,
            "monitor_models.py must derive paths from __file__ not hard-coded strings"
        )

    def test_retrain_uses_abspath_for_root(self):
        src = RETRAIN_PY.read_text(encoding="utf-8")
        self.assertTrue(
            "os.path.abspath" in src or "__file__" in src,
            "retrain_all.py must derive paths from __file__ not hard-coded strings"
        )


# =============================================================================
# Section 20 — Cross-cutting: exit-code contract
# =============================================================================

class TestExitCodeContract(unittest.TestCase):

    def test_monitor_main_block_calls_sys_exit(self):
        src = MONITOR_PY.read_text(encoding="utf-8")
        self.assertIn("sys.exit", src)

    def test_retrain_main_block_calls_sys_exit(self):
        src = RETRAIN_PY.read_text(encoding="utf-8")
        self.assertIn("sys.exit", src)

    def test_monitor_exit_codes_are_0_and_1_only(self):
        """run_monitor must return only 0 or 1."""
        tree = _ast_source(MONITOR_PY)
        returns = [
            n.value.n if isinstance(n.value, ast.Constant) else None
            for n in ast.walk(tree)
            if isinstance(n, ast.Return) and isinstance(n.value, ast.Constant)
        ]
        valid = {0, 1}
        for r in returns:
            if r is not None:
                self.assertIn(r, valid, f"run_monitor() returns unexpected value: {r}")

    def test_retrain_main_returns_0_or_1(self):
        tree    = _ast_source(RETRAIN_PY)
        returns = [
            n.value.n if isinstance(n.value, ast.Constant) else None
            for n in ast.walk(tree)
            if isinstance(n, ast.Return) and isinstance(n.value, ast.Constant)
        ]
        valid = {0, 1}
        for r in returns:
            if r is not None:
                self.assertIn(r, valid, f"main() returns unexpected value: {r}")

    def test_monitor_drift_exits_1(self):
        """The drift branch must return 1 — confirmed by source scan."""
        src = MONITOR_PY.read_text(encoding="utf-8")
        drift_idx = src.find("DRIFT DETECTED")
        self.assertGreater(drift_idx, 0)
        after_drift = src[drift_idx:]
        self.assertIn("return 1", after_drift)

    def test_monitor_ok_exits_0(self):
        """The clean branch must return 0."""
        src = MONITOR_PY.read_text(encoding="utf-8")
        ok_idx = src.find("[OK]")
        self.assertGreater(ok_idx, 0)
        after_ok = src[ok_idx:]
        self.assertIn("return 0", after_ok)


# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
