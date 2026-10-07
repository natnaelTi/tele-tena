#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd -- "$(dirname -- "$0")/.." && pwd)"
BENCH_DIR="$(cd -- "$APP_DIR/../.." && pwd)"
SITE="${TELE_TENA_TEST_SITE:-}"
BASE="${TELE_TENA_BROWSER_ORIGIN:-http://127.0.0.1:8017}"
FIXTURE="/tmp/tele-tena-availability-browser-$$.json"
trap 'rm -f -- "$FIXTURE"' EXIT

if [[ ! "$SITE" =~ ^tele-tena-[a-z0-9-]+\.localhost$ ]]; then
  echo "Set TELE_TENA_TEST_SITE to a disposable TeleTena .localhost site." >&2
  exit 2
fi

TELE_TENA_TEST_SITE="$SITE" TELE_TENA_AVAILABILITY_FIXTURE="$FIXTURE" \
  "$BENCH_DIR/env/bin/python" "$APP_DIR/scripts/prepare_availability_browser.py"
TELE_TENA_REVIEW_SITE_PATH="$BENCH_DIR/sites/$SITE" \
  TELE_TENA_AVAILABILITY_FIXTURE="$FIXTURE" \
  TELE_TENA_BROWSER_ORIGIN="$BASE" \
  NODE_PATH="/tmp/tele-tena-browser/node_modules" \
  node "$APP_DIR/scripts/browser-availability-regression.cjs"
