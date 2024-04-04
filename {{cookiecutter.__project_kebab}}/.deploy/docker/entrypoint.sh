#!/usr/bin/env sh

# Exit on first error
set -e

echo "Initializing database"
{{cookiecutter.__project_kebab}} --verbose db-init

echo "Upgrading database"
{{cookiecutter.__project_kebab}} --verbose db-upgrade

echo "Starting service"

# Start using 'exec' so SEGTERM and other signals are propagated
exec {{cookiecutter.__project_kebab}} run --host 0.0.0.0 --port 8000
