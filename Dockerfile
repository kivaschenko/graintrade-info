FROM python:3.11

ENV PGHOST=${PGHOST}
ENV PGUSER=${PGUSER}
ENV PGPORT=${PGPORT}
ENV PGDATABASE=${PGDATABASE}
ENV PGPASSWORD=${PGPASSWORD}

WORKDIR /app

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./pyproject.toml ./poetry.lock* /app/

RUN poetry install --no-root --no-dev

# Project initialization:
COPY . .

EXPOSE 3100

CMD ["gunicorn", "app.main:app"]

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
