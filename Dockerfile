FROM python:3.9-alpine

ENV PYTHONUNBUFFERED 1

EXPOSE 8000
WORKDIR /app

RUN apk --update --no-cache add gcc musl-dev libffi-dev openssl-dev python3-dev build-base

COPY poetry.lock pyproject.toml ./

RUN pip install poetry && \
    poetry config virtualenvs.in-project true && \
    poetry install --no-dev

COPY . ./

#CMD sleep infinity
CMD poetry run aerich upgrade && \
    poetry run uvicorn --host=0.0.0.0 app.main:app
