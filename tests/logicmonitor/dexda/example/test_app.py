# SPDX-FileCopyrightText: 2024 LogicMonitor, Inc.
#
# SPDX-License-Identifier: LicenseRef-All-rights-reserved

"""`logicmonitor.dexda.example.app` module tests."""

# mypy: disable-error-code="attr-defined"
# pylint: disable=protected-access

import unittest.mock

import pytest
import pytest_mock

import logicmonitor.dexda.example.app as lmd_example_app


class UtilityException(Exception):
    """Exception for utility purposes."""


@pytest.fixture(name="example_mock")
def fixture_example_mock() -> unittest.mock.Mock:
    """Create example mock.

    :returns: example mock.
    """
    mock = unittest.mock.Mock()
    return mock


def test_example_fn(
    mocker: pytest_mock.MockerFixture,
    example_mock: unittest.mock.Mock,
) -> None:
    """Test that `lmd_example_app.example_fn` correctly does something.

    :param mocker: pytest mocker.
    :param example_mock: example mock.
    """
    mocker.patch.object(grandparent.parent, "ExampleAttr")
