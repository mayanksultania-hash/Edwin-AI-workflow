..
   SPDX-FileCopyrightText: 2021, 2024 LogicMonitor, Inc.

   SPDX-License-Identifier: LicenseRef-All-rights-reserved

============
Contributing
============

.. contents::
   :local:
   :backlinks: none


Python style guide
==================

General
-------

Follow `PEP 8`_, with:

* Double quotation marks;
* Four spaces indentation;
* Hanging indentation;
* Absolute imports only;
* logicmonitor.dexda imports aliased as ``lmd_...``.

Format code with `Black`_'s preview style with a 79-character line length:

.. code-block:: sh

   black --preview --line-length=79


Docstrings
----------

Follow `PEP 257`_, with `Sphinx autodoc-style reStructuredText docstrings`_.

Document function/method signatures without type information (avoiding
duplication from type hints), e.g.:

.. code-block:: py

   """Do a thing.

   :param foo: description of foo.
   :param bar: description of bar.
   :returns: baz.
   :raises QuxError: if a thing happens.
   """


Signatures
----------

All functions/methods with more than one argument (excluding ``cls``,
``self`` etc.) should have keyword-only signatures:

.. code-block:: py

   def foo(bar: str):
       ...

   def foo(self, bar: str):
       ...

   def foo(*, bar: str, baz: str):
       ...

   def foo(self, *, bar: str, baz: str):
       ...


Type annotations
----------------

Annotate all functions, methods etc. according to `PEP 484`_ and `PEP 526`_.


Licensing
=========

Add licence information for every file per `REUSE`_, linting with ``reuse lint``.


Commit messages
===============

Follow `Conventional Commits`_, with the change type initial letter capitalised
(e.g. ``BREAKING CHANGE``, ``Feat``, ``Fix``).


Versioning
==========

Version according to `SemVer`_ versioning rules.


Bumping
-------

* Update CHANGELOG.rst per below.
* Bump version with ``inv version.bump-{major,minor,patch}`` (per SemVer).


Changelog
=========

* Update ``CHANGELOG.rst`` with changes grouped into ``BREAKING CHANGES``,
  ``Features``, and ``Fixes``.

  * Scoped if applicable.
  * In simple past tense.
  * E.g. ``Containers: added ... .``.

* Put unreleased changes under a section named ``Unreleased`` at the top.
* On release, migrate changes to their own section named
  ``<version> - <iso-8601-date>``, with versioned sections sorted in descending
  order, dropping empty change type subsections.


Development environment
=======================

* Python 3.12+.
* PDM (``pip3 install pdm``).
* Create ``.env`` from example:

  .. code-block:: sh

     cp docs/examples/dotenv .env

  * Populate values.

* Install to venv and activate:

  .. code-block:: sh

     pdm install --group=:all
     . <(pdm venv activate)


Testing
=======

.. code-block:: sh

   invoke tests.run


Python package
==============

Requirements
------------

Environmental AWS credentials (e.g. via ``AWS_ACCESS_KEY_ID`` and
``AWS_SECRET_ACCESS_KEY``) with read-write access to AWS ECR.


Building
--------

.. code-block:: sh

   invoke python-package.build


Publishing
----------

.. code-block:: sh

   invoke python-package.publish


Container image
===============

Requirements
------------

Environmental AWS credentials (e.g. via ``AWS_ACCESS_KEY_ID`` and
``AWS_SECRET_ACCESS_KEY``) with read-write access to AWS ECR and CodeArtifact.


Building
--------

.. code-block:: sh

   invoke container-image.build


Publishing
----------

.. code-block:: sh

   invoke container-image.publish


.. _Conventional Commits: https://www.conventionalcommits.org/en/v1.0.0/
.. _keep a changelog: https://keepachangelog.com/en/1.0.0/
.. _PEP 8: https://www.python.org/dev/peps/pep-0008/
.. _PEP 257: https://www.python.org/dev/peps/pep-0257/
.. _PEP 484: https://www.python.org/dev/peps/pep-0484/
.. _PEP 526: https://www.python.org/dev/peps/pep-0526/
.. _REUSE: https://reuse.software/
.. _SemVer: https://semver.org/
.. _Sphinx autodoc-style reStructuredText docstrings:
   https://www.sphinx-doc.org/en/master/tutorial/automatic-doc-generation.html
