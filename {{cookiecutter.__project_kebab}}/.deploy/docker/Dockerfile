FROM python:3.14-slim-trixie

WORKDIR /app

# postgresql driver build deps
RUN apt update && apt install -y build-essential libpq-dev python3-dev gcc

RUN pip install --no-input "uv"

# Install packages in a cache-friendly way
COPY uv.lock ./
COPY pyproject.toml ./

# Configure credentials for distribusion package repo
ARG GITLAB_REGISTRY_USERNAME
ARG GITLAB_REGISTRY_PASSWORD
ENV UV_INDEX_DISTRIBUSION_USERNAME=$GITLAB_REGISTRY_USERNAME
ENV UV_INDEX_DISTRIBUSION_PASSWORD=$GITLAB_REGISTRY_PASSWORD

RUN uv export --frozen --no-dev --no-editable --no-emit-project --format requirements.txt --output-file requirements.txt \
    && uv pip sync --system requirements.txt \
    && rm -f requirements.txt


# Copy package source code
COPY ./{{cookiecutter.__project_slug}} ./{{cookiecutter.__project_slug}}
COPY ./alembic ./alembic
COPY ./alembic.ini ./alembic.ini

# Install package
RUN uv pip install --system .

COPY .deploy/docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]
