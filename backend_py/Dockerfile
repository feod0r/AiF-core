FROM python:3.13.2-slim-bookworm AS build

# Install system dependencies
RUN apt-get update && apt-get install -y gnupg make curl wget sudo git gcc && apt-get update && rm -rf /var/lib/apt/lists/* && apt-get autoremove -y

# Install Poetry
ARG POETRY_VERSION=2.1
RUN pip install --no-cache-dir poetry==$POETRY_VERSION

# Configure Poetry
RUN poetry config virtualenvs.create true && \
  poetry config virtualenvs.in-project true && \
  poetry install --without dev --no-root

FROM python:3.13.2-slim-bookworm

COPY --from=build .venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY src src

ARG APP_VERSION
ARG COMMIT_SHORT
ENV APP_VERSION=$APP_VERSION
RUN export APP_VERSION=$APP_VERSION && \
  export COMMIT=$COMMIT_SHORT

ENTRYPOINT ["python", "src"]

