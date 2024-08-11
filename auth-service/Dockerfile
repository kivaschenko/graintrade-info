FROM python:3.11

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

# CMD ["gunicorn", "app.main:app"]

# Run the application:
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
