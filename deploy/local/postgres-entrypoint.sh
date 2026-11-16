#!/bin/sh
set -eu
mkdir -p /var/lib/postgresql/tls
cp /run/tls/db.crt /var/lib/postgresql/tls/db.crt
cp /run/tls/db.key /var/lib/postgresql/tls/db.key
chown postgres:postgres /var/lib/postgresql/tls/db.*
chmod 600 /var/lib/postgresql/tls/db.key
exec docker-entrypoint.sh postgres -c ssl=on \
  -c hba_file=/opt/sr/pg_hba.conf \
  -c ssl_cert_file=/var/lib/postgresql/tls/db.crt \
  -c ssl_key_file=/var/lib/postgresql/tls/db.key
