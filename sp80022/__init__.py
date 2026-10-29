"""Own implementation of the NIST SP 800-22 Rev. 1a statistical test battery (feature 002).

Replaces nistrng 1.2.3 as the judge (research R1, defects N4-N9). It does not depend on
`phycoweb`. Passing these tests does not show cryptographic security.
"""
import hashlib
from pathlib import Path
from typing import List

import numpy

from . import tests
from .assess import assess
from .special import TestResult
from .tests_template import templates

__version__ = "1.0.0"

__all__ = ["battery", "templates", "assess", "source_sha256", "tests", "TestResult",
           "__version__"]


def battery(bits) -> List[TestResult]:
    """Run all 15 tests in SP 800-22 order; each gets a read-only view of the input."""
    arr = numpy.asarray(bits)
    results = []
    for test in tests.ORDER:
        view = arr.view()
        view.flags.writeable = False
        results.append(test(view))
    return results


def source_sha256() -> str:
    """SHA-256 over this package's .py files, sorted by path, with LF line endings."""
    h = hashlib.sha256()
    pkg = Path(__file__).resolve().parent
    for path in sorted(pkg.glob("*.py")):
        h.update(path.name.encode("utf-8") + b"\0")
        h.update(path.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()
