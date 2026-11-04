# Online dependency build only. No candidate source or hooks enter this image build.
FROM python@sha256:f21c0d5a44c56805654c15abccc1b2fd576c8d93aca0a3f74b4aba2dc92510e2
COPY requirements.lock /requirements.lock
RUN python -m pip install --no-cache-dir --only-binary=:all: --require-hashes -r /requirements.lock && python -m pip check
USER 65534:65534
WORKDIR /repo
