"""
Functional tests for the QA test-generation engine.

These exercise the core value of the toolkit — turning page-analysis data into
runnable test suites — and assert that the generated test files are
syntactically valid Python (compiled via ``ast.parse``). No browser is needed:
the generators emit source code from data.
"""

from __future__ import annotations

import ast

from core.automated_qa_orchestrator import QATestConfig, QATestGenerator


def _generator() -> QATestGenerator:
    return QATestGenerator(QATestConfig(), log_callback=lambda _msg: None)


# ── QATestConfig ─────────────────────────────────────────────────────────────

def test_config_defaults_total_is_sum_of_counts():
    cfg = QATestConfig()
    assert cfg.get_total_tests() == sum(cfg.test_counts.values())
    assert cfg.test_counts["functional"] >= 1


def test_config_accepts_custom_counts():
    cfg = QATestConfig({"functional": 3, "negative": 2})
    assert cfg.get_total_tests() == 5


# ── Generated suites are valid Python ────────────────────────────────────────

def test_functional_suite_is_valid_python(tmp_path):
    gen = _generator()
    result = gen.generate_functional_tests({"url": "https://example.com"}, tmp_path)

    assert isinstance(result, list)
    test_file = tmp_path / "test_functional.py"
    assert test_file.exists()

    content = test_file.read_text(encoding="utf-8")
    assert "TestFunctionalSuite" in content
    assert "https://example.com" in content
    ast.parse(content)  # must be syntactically valid Python


def test_negative_suite_is_valid_python(tmp_path):
    gen = _generator()
    gen.generate_negative_tests({"url": "https://example.com"}, tmp_path)

    generated = list(tmp_path.glob("test_*.py"))
    assert generated, "no test file generated"
    for f in generated:
        ast.parse(f.read_text(encoding="utf-8"))


def test_accessibility_suite_is_valid_python(tmp_path):
    gen = _generator()
    gen.generate_accessibility_tests({"url": "https://example.com"}, tmp_path)

    generated = list(tmp_path.glob("test_*.py"))
    assert generated
    for f in generated:
        ast.parse(f.read_text(encoding="utf-8"))
