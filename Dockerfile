FROM python:3.9

ENV PYTHONUNBUFFERED 1

EXPOSE 8000
WORKDIR /code

RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry --no-cache-dir
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.in-project true \
    && poetry config virtualenvs.create false \
    && poetry config experimental.new-installer false \
    && poetry install --no-dev --no-interaction --no-ansi

COPY . /code/

#CMD sleep infinity
CMD aerich upgrade && \
    uvicorn --host=0.0.0.0 app.main:app
