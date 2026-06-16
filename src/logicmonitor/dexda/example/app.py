# SPDX-FileCopyrightText: 2024 LogicMonitor, Inc.
#
# SPDX-License-Identifier: LicenseRef-All-rights-reserved

"""Example."""

import importlib.metadata
import logging
import typing

import typer

import logicmonitor.dexda.example.logging as lmd_example_logging

_ENV_PREFIX = "EXAMPLE_"


def ver_callback(version_flag: bool) -> None:
    """Print version and exit if version flag set.

    :param version_flag: version flag value.
    :raises SystemExit: if version flag is true.
    """
    if version_flag:
        print(importlib.metadata.version(__package__))
        raise SystemExit


app = typer.Typer()


@app.command(help=__doc__)
def main(
    *,
    example: typing.Annotated[
        str, typer.Option(envvar=f"{_ENV_PREFIX}EXAMPLE")],
    version: typing.Annotated[
        bool, typer.Option("--version", callback=ver_callback, is_eager=True)
    ] = False,
    logging_level: lmd_example_logging.LevelName = (
        lmd_example_logging.LevelName.INFO),
) -> None:
    """Example.

    :param example: example.
    :param version: whether to only print version and exit.
    :param logging_level: logging level.
    """
    ver_callback(version)
    lmd_example_logging.initialise_from_name(level_name=logging_level)
    logging.debug("Example.")
