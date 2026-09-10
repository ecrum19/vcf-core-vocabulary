#!/bin/sh
# Run a repository Python script with the project virtualenv when one exists,
# falling back to the system interpreter. Every npm script that invokes Python
# goes through here so the selection lives in one place instead of being
# repeated inline. Run from the repository root (npm scripts already are).
set -eu
if [ -x .venv/bin/python ]; then
  exec .venv/bin/python "$@"
fi
exec python3 "$@"
