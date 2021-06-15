#!/usr/bin/env bash

set -euxo pipefail

# Show which versions we installed, for transparency / debugging
pipenv run pip list

# Assemble Lambda
OLD_PWD=$(pwd)
cd "$(pipenv --venv)/lib/python3.6/site-packages"
zip -q -r9 "${OLD_PWD}/lambda.zip" .
cd "${OLD_PWD}"
zip -q -r9 -g lambda.zip ./*.py
