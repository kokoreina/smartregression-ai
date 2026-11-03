# Dependency image only: no candidate source or project workspace is a build input.
FROM python@sha256:f21c0d5a44c56805654c15abccc1b2fd576c8d93aca0a3f74b4aba2dc92510e2
RUN python -m pip install --no-cache-dir pytest==9.1.1 pytest-cov==7.0.0 build==1.3.0 hatchling==1.27.0
USER 65534:65534
WORKDIR /repo
