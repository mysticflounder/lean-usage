# Copyright (c) 2026 Adam McKenna
# Released under GPL-3.0-or-later as described in the file LICENSE.
# Author: Adam McKenna <adam@mysticflounder.ai>
# Purpose: isolated Linux runtime for the plugin release smoke test.
# Usage: bash scripts/test-docker.sh
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim@sha256:e5b65587bce7de595f299855d7385fe7fca39b8a74baa261ba1b7147afa78e58
RUN apt-get update && apt-get install -y --no-install-recommends bash jq elan ca-certificates git \
    && apt-get clean
ARG LEAN_TOOLCHAIN=leanprover/lean4:v4.28.0
RUN elan toolchain install "${LEAN_TOOLCHAIN}" && elan default "${LEAN_TOOLCHAIN}"
ENV PATH="/root/.elan/bin:${PATH}"
WORKDIR /work
