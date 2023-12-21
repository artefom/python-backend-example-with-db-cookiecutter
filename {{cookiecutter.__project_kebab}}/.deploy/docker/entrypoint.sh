#!/usr/bin/env sh

# Exit on first error
set -e

echo "Initializing database"
{{cookiecutter.__project_kebab}} --verbose db-init

echo "Upgrading database"
{{cookiecutter.__project_kebab}} --verbose db-upgrade

# Start single uvicorn worker
# NOTE: Sigterm might not be propagated propelry, use
# CMD python {{cookiecutter.__project_slug}}/main.py
# If graceful termination is needed

{{cookiecutter.__project_kebab}} run --host 0.0.0.0 --port 8000
