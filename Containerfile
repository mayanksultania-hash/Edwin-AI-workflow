# SPDX-FileCopyrightText: 2021, 2023-2025 LogicMonitor, Inc.
#
# SPDX-License-Identifier: LicenseRef-All-rights-reserved

FROM registry.fedoraproject.org/fedora-minimal:41

ARG PIP_INDEX_URL
ARG PROJ_MAINTAINER_NAME
ARG PROJ_NAME
ARG PROJ_VER
ARG PROJ_DESCR
LABEL maintainer="$PROJ_MAINTAINER_NAME"
LABEL description="$PROJ_DESCR"

RUN dnf install -y \
        python3-pip \
        tini \
    && dnf clean all \
    && pip3 install "$PROJ_NAME==$PROJ_VER"

ENTRYPOINT ["/usr/bin/tini", "--"]
ENV PYTHONUNBUFFERED=x
CMD ["example"]
