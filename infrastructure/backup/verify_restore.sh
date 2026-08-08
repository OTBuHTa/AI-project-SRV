#!/bin/sh
set -eu

: "${BACKUP_DUMP:?BACKUP_DUMP is required}"

PGHOST="${PGHOST:-postgres}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-aisrv}"
PGDATABASE="${PGDATABASE:-postgres}"
EXPECTED_REVISION="${EXPECTED_REVISION:-0007_backup_pipeline}"
MIN_TABLE_COUNT="${MIN_TABLE_COUNT:-17}"

if [ ! -f "$BACKUP_DUMP" ]; then
    echo "ERROR: dump not found: $BACKUP_DUMP" >&2
    exit 10
fi

RESTORE_DB="aisrv_restore_$(date +%s)_$$"

cleanup() {
    echo "Dropping temporary database: $RESTORE_DB"
    dropdb \
        --if-exists \
        --host="$PGHOST" \
        --port="$PGPORT" \
        --username="$PGUSER" \
        "$RESTORE_DB" >/dev/null 2>&1 || true
}

trap cleanup EXIT INT TERM

echo "Creating temporary database: $RESTORE_DB"

createdb \
    --host="$PGHOST" \
    --port="$PGPORT" \
    --username="$PGUSER" \
    "$RESTORE_DB"

echo "Restoring: $BACKUP_DUMP"

pg_restore \
    --host="$PGHOST" \
    --port="$PGPORT" \
    --username="$PGUSER" \
    --dbname="$RESTORE_DB" \
    --no-owner \
    --no-privileges \
    --exit-on-error \
    "$BACKUP_DUMP"

REVISION="$(
    psql \
        --host="$PGHOST" \
        --port="$PGPORT" \
        --username="$PGUSER" \
        --dbname="$RESTORE_DB" \
        --tuples-only \
        --no-align \
        --command="SELECT version_num FROM alembic_version;" \
        | tr -d '[:space:]'
)"

if [ "$REVISION" != "$EXPECTED_REVISION" ]; then
    echo "ERROR: expected Alembic revision $EXPECTED_REVISION, got $REVISION" >&2
    exit 20
fi

TABLE_COUNT="$(
    psql \
        --host="$PGHOST" \
        --port="$PGPORT" \
        --username="$PGUSER" \
        --dbname="$RESTORE_DB" \
        --tuples-only \
        --no-align \
        --command="SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" \
        | tr -d '[:space:]'
)"

if [ "$TABLE_COUNT" -lt "$MIN_TABLE_COUNT" ]; then
    echo "ERROR: expected at least $MIN_TABLE_COUNT public tables, got $TABLE_COUNT" >&2
    exit 30
fi

echo "RESTORE_VERIFIED=true"
echo "ALEMBIC_REVISION=$REVISION"
echo "PUBLIC_TABLE_COUNT=$TABLE_COUNT"
