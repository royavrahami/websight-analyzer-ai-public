"""
Import smoke tests for the websight-analyzer package.

These are the project's first automated tests. They guard the package-import
structure: every core module must import cleanly as ``core.<module>`` (i.e.
without relying on runtime ``sys.path`` manipulation), and the integrated
analyzer must resolve to its *full* mixin class rather than the degraded
import-error fallback.

Each check runs in a fresh subprocess so that module-level import side effects
(logging stream setup in the large analyzer module) do not interact with
pytest's output capture. The subprocess inherits the repo-root working
directory, so ``import core.<module>`` resolves the package directly.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

CORE_MODULES = [
    "core.playwright_web_elements_analyzer",
    "core.element_detection_extensions",
    "core.output_extensions",
    "core.integrated_web_analyzer",
    "core.advanced_analysis",
    "core.automated_qa_orchestrator",
    "core.web_element_spider",
]


def _run(code: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("module_name", CORE_MODULES)
def test_core_module_imports(module_name: str) -> None:
    """Each core module imports cleanly as a package submodule."""
    result = _run(f"import {module_name}")
    assert result.returncode == 0, f"importing {module_name} failed:\n{result.stderr}"


def test_integrated_analyzer_resolves_full_mixin() -> None:
    """`IntegratedWebElementAnalyzer` is the full mixin class, not the fallback.

    Before the packaging fix, importing this module as ``core.integrated_web_analyzer``
    silently fell back to a stripped-down stub (bases == (object,)) because the
    sibling imports were unqualified. The fully-qualified ``core.*`` imports make
    the real, feature-complete class load deterministically.
    """
    code = (
        "from core.integrated_web_analyzer import IntegratedWebElementAnalyzer as C\n"
        "assert C.__bases__ != (object,), 'fallback stub loaded instead of full mixin'\n"
        "a = C(headless=True)\n"
        "assert hasattr(a, 'analyze_url'), 'analyze_url missing'\n"
    )
    result = _run(code)
    assert result.returncode == 0, result.stderr
