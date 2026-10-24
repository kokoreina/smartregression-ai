ARG PYTHON_IMAGE=python@sha256:35caba83af2fe6da9a5d922f9b0156f21d1246a48278c58a08bd253303ba42e8
FROM ${PYTHON_IMAGE}
RUN python -m pip install --no-cache-dir pytest==9.1.1 iniconfig==2.3.0 packaging==26.3 pluggy==1.6.0 pygments==2.21.0
USER 65534:65534
WORKDIR /input
