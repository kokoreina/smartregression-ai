# Fixture image only. Resolve BASE_IMAGE to an official Python digest before build.
ARG BASE_IMAGE=python@sha256:f21c0d5a44c56805654c15abccc1b2fd576c8d93aca0a3f74b4aba2dc92510e2
FROM ${BASE_IMAGE}
RUN python -m pip install --no-cache-dir pytest==9.1.1
USER 65534:65534
WORKDIR /repo
