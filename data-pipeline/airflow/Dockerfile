# Airflow 3.x — custom image for GrainTrade scheduler
#
# Based on the official Apache Airflow image.
# Python 3.12 is used to match the data-pipeline service.
#
# Pin to a specific patch version in production, e.g.:
#   apache/airflow:3.0.0-python3.12
FROM apache/airflow:3.0.0

# Switch to root only to install OS-level dependencies (if any)
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Drop back to the airflow user for pip installs (required by the base image)
USER airflow

# Install extra Python packages on top of the base Airflow installation.
# The base image already provides: apache-airflow, requests, pendulum, etc.
COPY requirements.txt /tmp/airflow-requirements.txt
RUN pip install --no-cache-dir -r /tmp/airflow-requirements.txt
