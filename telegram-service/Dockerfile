FROM python:3.11-slim
WORKDIR /telegram-service
RUN apt-get update && apt-get install -y curl && \
    curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false
COPY . .
RUN poetry install
CMD [ "python", "app/main.py" ]