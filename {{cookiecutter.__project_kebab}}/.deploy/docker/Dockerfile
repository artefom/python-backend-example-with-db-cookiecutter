FROM python:3.13-slim-bullseye

WORKDIR /app

# postgresql driver build deps
RUN apt update && apt install -y build-essential libpq-dev python3-dev gcc

RUN pip install --no-input "poetry>=2.0.0,<3.0.0"

# Install packages in a cache-friendly way
COPY poetry.lock ./
COPY pyproject.toml ./

# Configure credentials for distribusion pacakge repo
ARG GITLAB_REGISTRY_USERNAME
ARG GITLAB_REGISTRY_PASSWORD
RUN poetry config http-basic.distribusion $GITLAB_REGISTRY_USERNAME $GITLAB_REGISTRY_PASSWORD

RUN POETRY_VIRTUALENVS_CREATE=false poetry install --no-root

# Copy package source code
COPY ./{{cookiecutter.__project_slug}} ./{{cookiecutter.__project_slug}}
COPY ./alembic ./alembic
COPY ./alembic.ini ./alembic.ini

# Install package
RUN pip install --no-deps .

COPY .deploy/docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]
