FROM python:3.9-alpine

ENV PYTHONUNBUFFERED 1

EXPOSE 8000
WORKDIR /code

RUN apk --update --no-cache add gcc musl-dev libffi-dev openssl-dev python3-dev build-base

RUN pip install poetry --no-cache-dir
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.in-project true \
    && poetry config experimental.new-installer false \
    && poetry install --no-dev --no-interaction --no-ansi

COPY . /code/

#CMD sleep infinity
CMD poetry run aerich upgrade && \
    poetry run uvicorn --host=0.0.0.0 app.main:app
