# SPDX-FileCopyrightText: 2023, 2024 LogicMonitor, Inc.
#
# SPDX-License-Identifier: LicenseRef-All-rights-reserved

"""Logging functionality."""

import enum
import logging


class LevelName(enum.StrEnum):
    """Logging level names (for CLI use)."""

    CRITICAL = enum.auto()
    ERROR = enum.auto()
    WARNING = enum.auto()
    INFO = enum.auto()
    DEBUG = enum.auto()


class Level(enum.IntEnum):
    """Logging levels (as levels in `logging` are not an enum)."""

    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG


def initialise(*, level: Level) -> None:
    """Initialise logging.

    :param level: logging level.
    """
    logging.captureWarnings(True)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s: %(levelname)-8s: %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z"))
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(handler)


def initialise_from_name(*, level_name: LevelName) -> None:
    """Initialise logging from logging level name.

    :param level_name: logging level.
    """
    logging_level_int = Level[LevelName(level_name).name]
    initialise(level=logging_level_int)
