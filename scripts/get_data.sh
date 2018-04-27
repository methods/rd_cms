#!/usr/bin/env bash

set -o pipefail

if [ "$#" -ne 2 ]; then
  echo "Required args [postgres url] and [output file and path]" >&2
  echo "e.g. ./get_data.sh postgres://[username]:[password]@[host]:[port]/[db] /tmp/data.dump"
  exit 1
fi

pg_dump --no-acl --no-owner --data-only -Fc -T users -T alembic_version -T build -d $1 > $2
