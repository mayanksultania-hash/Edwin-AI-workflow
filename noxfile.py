# SPDX-FileCopyrightText: 2021, 2023, 2024 LogicMonitor, Inc.
#
# SPDX-License-Identifier: LicenseRef-All-rights-reserved

"""Run Nox sessions.

Usage:
  nox [-s <session>-<ver>]
"""

import collections.abc
import pathlib
import sys
import typing

import nox
import packaging.specifiers
import tomlkit

_PROJ_ROOT_PATH = pathlib.Path(__file__).parent
_PROJ_CFG_PATH = _PROJ_ROOT_PATH / "pyproject.toml"
_BUILD_DIR_REL_PATH = "build"
_PDM_INSTALL_CMD = ["pdm", "--ignore-python", "install", "--group=:all"]


def get_pyfile_path_strs() -> collections.abc.Iterator[str]:
    """Get all Python file paths recursively as strings.

    :returns: Python file paths.
    """
    return (
        str(p) for p in _PROJ_ROOT_PATH.rglob("*.py")
        if p.relative_to(_PROJ_ROOT_PATH).parts[0] != _BUILD_DIR_REL_PATH
        and not p.relative_to(_PROJ_ROOT_PATH).parts[0].startswith("."))


def _get_python_vers() -> list[str]:
    """Gen. Python 3 minor ver's up to current, filtered by proj's req.

    :returns: Python versions.
    """
    proj_conf: dict[str, typing.Any] = tomlkit.loads(
        _PROJ_CFG_PATH.read_text())
    py_req = proj_conf["project"]["requires-python"]
    specifier = packaging.specifiers.Specifier(py_req)
    candidate_vers = (
        f"3.{minor}" for minor in range(0, sys.version_info.minor + 1))
    return list(str(ver) for ver in specifier.filter(candidate_vers))


_PYTHON_VERS = _get_python_vers()


@nox.session(python=_PYTHON_VERS)
def bandit(session: nox.sessions.Session) -> None:
    """Run `bandit`.

    :param session: Nox Session object.
    """
    session.run_always(*_PDM_INSTALL_CMD, external=True, silent=True)
    session.run(
        "python3",
        "-m",
        "bandit",
        "-q",
        "--format=custom",
        "--msg-template={relpath}:{line}:0: {test_id}: {severity}: {msg}",
        "--skip=B404",
        *get_pyfile_path_strs())


@nox.session(python=_PYTHON_VERS)
def mypy(session: nox.sessions.Session) -> None:
    """Run mypy.

    :param session: Nox Session object.
    """
    session.run_always(*_PDM_INSTALL_CMD, external=True, silent=True)
    session.run(
        "python3",
        "-m",
        "mypy",
        "--no-error-summary",
        "--show-column-numbers",
        "--show-error-codes",
        "--strict",
        "--explicit-package-bases",
        *get_pyfile_path_strs(),
        env={"MYPYPATH": "src"})


@nox.session(python=_PYTHON_VERS)
def pycodestyle(session: nox.sessions.Session) -> None:
    """Run `pycodestyle`.

    :param session: Nox Session object.
    """
    session.run_always(*_PDM_INSTALL_CMD, external=True, silent=True)
    session.run(
        "python3",
        "-m",
        "pycodestyle",
        "--max-doc-length=72",
        *get_pyfile_path_strs())


@nox.session(python=_PYTHON_VERS)
def pydocstyle(session: nox.sessions.Session) -> None:
    """Run `pydocstyle`.

    :param session: Nox Session object.
    """
    session.run_always(*_PDM_INSTALL_CMD, external=True, silent=True)
    session.run("python3", "-m", "pydocstyle")


@nox.session(python=_PYTHON_VERS)
@nox.parametrize(
    "checks",
    [
        nox.param("parameter_documentation", id="parameter_documentation"),
        nox.param("design", id="design"),
        nox.param("miscellaneous", id="miscellaneous"),
        nox.param("similarities", id="similarities"),
        nox.param("others", id="others")])
def pylint(session: nox.sessions.Session, checks: str) -> None:
    """Run `pylint`.

    :param session: Nox Session object.
    :param checks: name of checks group to run (parameter_documentation,
        design, miscellaneous, similarities or others).
    :raises ValueError: if invalid test group(s) provided.
    """
    if checks == "parameter_documentation":
        group_args = ["--disable=all", "--enable=parameter_documentation"]
    elif checks == "design":
        group_args = ["--disable=all", "--enable=design"]
    elif checks == "miscellaneous":
        group_args = ["--disable=all", "--enable=miscellaneous"]
    elif checks == "similarities":
        group_args = ["--disable=all", "--enable=similarities"]
    elif checks == "others":
        group_args = [
            "--disable=parameter_documentation,design,miscellaneous"
            ",similarities"]
    else:
        raise ValueError("Invalid checks group.")
    session.run_always(*_PDM_INSTALL_CMD, external=True, silent=True)
    session.run(
        "python3",
        "-m",
        "pylint.__main__",
        "--load-plugins=pylint.extensions.docparams",
        "--no-docstring-rgx=^$",
        "--accept-no-param-doc=false",
        "--accept-no-raise-doc=false",
        "--accept-no-return-doc=false",
        "--accept-no-yields-doc=false",
        "--max-line-length=79",
        "--score=n",
        *group_args,
        *get_pyfile_path_strs())


@nox.session(python=_PYTHON_VERS)
def pytest(session: nox.sessions.Session) -> None:
    """Run `pytest`.

    :param session: Nox Session object.
    """
    session.run_always(*_PDM_INSTALL_CMD, external=True, silent=True)
    session.run("python3", "-m", "pytest", "-qq")


@nox.session(python=_PYTHON_VERS)
def coverage(session: nox.sessions.Session) -> None:
    """Run `coverage`.

    :param session: Nox Session object.
    """
    session.run_always(*_PDM_INSTALL_CMD, external=True, silent=True)
    session.run(
        "python3",
        "-m",
        "coverage",
        "run",
        "--branch",
        "-m",
        "pytest",
        "-qq")
    session.run(
        "python3",
        "-m",
        "coverage",
        "report",
        "--fail-under=100",
        "--show-missing")


@nox.session(python=_PYTHON_VERS)
def reuse(session: nox.sessions.Session) -> None:
    """Run `reuse`.

    :param session: Nox Session object.
    """
    session.run("reuse", "lint", "-q", external=True)
