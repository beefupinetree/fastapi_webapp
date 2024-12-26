FROM python:3.12-slim-bookworm

WORKDIR /backend

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERED 1

# install system dependencies
RUN apt-get update \
    && apt-get -y install netcat-traditional gcc postgresql \
    && apt-get clean

# install python dependencies
RUN pip install --upgrade pip
# RUN pip uninstall psycopg2
# RUN pip install --upgrade wheel setuptools uv
RUN pip install uv
# COPY ./requirements.txt /backend/requirements.txt
COPY ./pyproject.toml /backend/pyproject.toml
RUN pip install .

COPY . /backend

