FROM python:3.11-slim

LABEL authors="vmoroz"

ARG TOKEN
ARG SQLALCHEMY_URL

RUN echo $TOKEN

ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.1 \
    TOKEN=${TOKEN} \
    SQLALCHEMY_URL=${SQLALCHEMY_URL}

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl

RUN curl -sSL https://install.python-poetry.org | python3 - --version ${POETRY_VERSION} --yes
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY pyproject.toml /app
COPY poetry.lock /app
COPY ./src /app

RUN poetry config virtualenvs.create false
RUN poetry install --no-dev --no-interaction --no-ansi

CMD [ "python3", "/app/run.py"]