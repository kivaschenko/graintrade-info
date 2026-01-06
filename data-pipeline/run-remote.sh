#!/usr/bin/env bash
set -euo pipefail

# run-remote.sh - wrapper to submit a job to a remote Spark master (production)
# Usage:
#   ./run-remote.sh <app.py> [-- <app-args>]
# Environment vars you can set before running:
#   SPARK_MASTER        (e.g. spark://1.2.3.4:7077) - required if not passed below
#   SPARK_HOME          (path to Spark distribution with spark-submit)
#   PYSPARK_PYTHON      (path to python interpreter for executors; default: venv python)
#   PYSPARK_DRIVER_PYTHON (path to python for driver; default same as PYSPARK_PYTHON)
#   DRIVER_HOST         (your reachable dev machine IP; default auto-detected)
#   EXTRA_PACKAGES      (comma-separated maven packages to pass to --packages)

show_help() {
  sed -n '1,120p' "$0" | sed -n '1,28p'
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  show_help
  exit 0
fi

# Application path is first argument
if [ $# -lt 1 ]; then
  echo "Usage: $0 <app.py> [-- <app-args>]"
  exit 2
fi

APP="$1"
shift || true

# Allow passing app args after --
APP_ARGS=()
if [ "$#" -gt 0 ]; then
  # if first remaining arg is --, drop it
  if [ "$1" = "--" ]; then
    shift
  fi
  APP_ARGS=("$@")
fi

# Defaults
: "${SPARK_MASTER:=}"  # must be set by user or edited below
: "${SPARK_HOME:=/opt/spark}"  # common location for system Spark
: "${PYSPARK_PYTHON:=/usr/bin/python3}"
: "${PYSPARK_DRIVER_PYTHON:=$PYSPARK_PYTHON}"
: "${EXTRA_PACKAGES:=}"

# Detect a sensible DRIVER_HOST if not provided (tries ip route)
: "${DRIVER_HOST:=}"
if [ -z "$DRIVER_HOST" ]; then
  # find default interface IP
  DRIVER_HOST=$(ip route get 1.1.1.1 2>/dev/null | awk '/src/ {print $7; exit}') || true
  DRIVER_HOST=${DRIVER_HOST:-127.0.0.1}
fi

if [ -z "$SPARK_MASTER" ]; then
  echo "ERROR: SPARK_MASTER not set. Export SPARK_MASTER='spark://HOST:7077' or edit this script."
  exit 3
fi

# Verify spark-submit
if [ ! -x "$SPARK_HOME/bin/spark-submit" ]; then
  echo "ERROR: spark-submit not found at $SPARK_HOME/bin/spark-submit" >&2
  exit 4
fi

export PYSPARK_PYTHON
export PYSPARK_DRIVER_PYTHON

CMD=("$SPARK_HOME/bin/spark-submit" "--master" "$SPARK_MASTER" "--deploy-mode" "client"
     --conf "spark.driver.host=$DRIVER_HOST" --conf "spark.driver.bindAddress=0.0.0.0")

if [ -n "$EXTRA_PACKAGES" ]; then
  CMD+=(--packages "$EXTRA_PACKAGES")
fi

# Pass-through additional spark-submit options via SPARK_SUBMIT_OPTS env var
if [ -n "${SPARK_SUBMIT_OPTS:-}" ]; then
  # shellsplit SPARK_SUBMIT_OPTS (simple split on spaces)
  read -r -a extra <<< "$SPARK_SUBMIT_OPTS"
  CMD+=("${extra[@]}")
fi

CMD+=("$APP")
if [ ${#APP_ARGS[@]} -gt 0 ]; then
  CMD+=("--" "${APP_ARGS[@]}")
fi

echo "Running: ${CMD[*]}"
exec "${CMD[@]}"
