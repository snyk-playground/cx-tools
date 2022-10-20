# This is a multistage container builder for poetry projects

FROM python:3.9-slim AS requirements

ENV PYTHONDONTWRITEBYTECODE 1
#ENV POETRY_VIRTUALENVS_CREATE false

# step one is to create a container with poetry on it
RUN python -m pip install --quiet -U pip poetry

WORKDIR /src

COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock

RUN poetry export --quiet --no-interaction -f requirements.txt --without-hashes -o /src/requirements.txt

# now we create our final container, runtime
FROM python:3.9-slim AS runtime

ENV PYTHONPATH /app
# cannot use WORKDIR with github action containers
RUN mkdir /app

# copy stuff from this repo into the /app directory of the container
COPY ci_scripts_library /app/ci_scripts_library

# now we use multistage containers to then copy the requirements from the other container
COPY --from=requirements /src/requirements.txt .

# now we're *just* deploying the needed packages for whatever was in the poetry setup
RUN python -m pip install --quiet -U pip
RUN pip install -r requirements.txt

COPY scripts/entrypoint.sh /usr/local/bin/

ENTRYPOINT ["bash", "/usr/local/bin/entrypoint.sh"]
