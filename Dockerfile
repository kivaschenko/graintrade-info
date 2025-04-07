# FROM python:3.11-slim
# WORKDIR /item-service
# # Install curl and Poetry
# RUN apt-get update && apt-get install -y curl && \
#     curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
#     cd /usr/local/bin && \
#     ln -s /opt/poetry/bin/poetry && \
#     poetry config virtualenvs.create false
# COPY . .
# RUN poetry install
# # CMD ["gunicorn", "app.main:app"]
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 1: Build stage
FROM python:3.12-slim AS builder
WORKDIR /graintrade-api

# Install curl and Poetry
RUN apt-get update && apt-get install -y curl && \
    curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

# Copy only the necessary files for dependency installation
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

# Copy the rest of the application code
COPY . .
COPY .env .env

# Stage 2: Final stage
FROM python:3.12-slim
WORKDIR /graintrade-api

# Copy the installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /graintrade-api /graintrade-api/
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
