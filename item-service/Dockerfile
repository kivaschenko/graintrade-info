FROM python:3.11.9

WORKDIR /item-service


# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./item-service/pyproject.toml ./item-service/poetry.lock* /item-service/

RUN poetry install

# Project initialization:
COPY ./item-service .

# CMD ["gunicorn", "app.main:app"]

# Run the application:
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
