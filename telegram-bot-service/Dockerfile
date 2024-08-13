FROM python:3.11.9
WORKDIR /telegram-bot-service

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

COPY ./telegram-bot-service/pyproject.toml ./telegram-bot-service/poetry.lock* /telegram-bot-service/
RUN poetry install
COPY ./telegram-bot-service .
CMD [ "python", "app/main.py" ]