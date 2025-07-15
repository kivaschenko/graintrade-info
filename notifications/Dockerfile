# Stage 1: Build stage
FROM python:3.12-slim AS builder
WORKDIR /notifications

# Install curl and Poetry
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy only the necessary files for dependency installation
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the application code
COPY . .

# Stage 2: Final stage
FROM python:3.12-slim

# Set the working directory
WORKDIR /notifications

# Copy the installed dependencies and application code from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /notifications /notifications

# Expose the application port
EXPOSE 8002

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]
