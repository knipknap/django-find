"""Nox sessions for testing django-find across Python × Django versions.

Run the full matrix:       nox
Run a single combo:        nox -s "tests(python='3.12', django='5.2')"
List all sessions:         nox -l
"""

import nox

nox.options.default_venv_backend = "uv"
nox.options.reuse_existing_virtualenvs = True

# ---------------------------------------------------------------------------
# Python × Django test matrix
#
# Only combinations where Django officially supports the Python version.
# Django 4.2 LTS : Python 3.8 – 3.12   (we start at 3.10)
# Django 5.1     : Python 3.10 – 3.13
# Django 5.2 LTS : Python 3.10 – 3.13
# Django 6.0     : Python 3.12 – 3.13
# ---------------------------------------------------------------------------
DJANGO_PYTHON_MATRIX: dict[str, list[str]] = {
    "4.2": ["3.10", "3.11", "3.12"],
    "5.1": ["3.10", "3.11", "3.12", "3.13"],
    "5.2": ["3.10", "3.11", "3.12", "3.13"],
    "6.0": ["3.12", "3.13"],
}


@nox.parametrize(
    "python,django",
    [
        (py, dj)
        for dj, pys in DJANGO_PYTHON_MATRIX.items()
        for py in pys
    ],
)
@nox.session
def tests(session: nox.Session, django: str) -> None:
    """Run pytest for a specific Python × Django combination."""
    django_spec = f"Django>={django},<{django.split('.')[0]}.{int(django.split('.')[1]) + 1}"
    session.install("-e", ".", f"{django_spec}", "pytest", "pytest-django")
    session.run("pytest", "tests/", "--verbosity=2", *session.posargs)


@nox.session(python="3.12")
def coverage(session: nox.Session) -> None:
    """Run tests with coverage reporting (latest Django)."""
    session.install("-e", ".", "pytest", "pytest-django", "coverage[toml]")
    session.run("coverage", "run", "-m", "pytest", "tests/", "--verbosity=2")
    session.run("coverage", "report", "--fail-under=70")
    session.run("coverage", "html")
    session.log("HTML report: htmlcov/index.html")
