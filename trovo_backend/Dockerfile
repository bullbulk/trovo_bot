FROM python:3.11-slim-buster

#ENV PYTHONDONTWRITEBYTECODE 1
#ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code

RUN pip install poetry
COPY poetry.lock pyproject.toml /code/

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi

COPY . /code/

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "app.trovo_bot.main:app", "--port", "8000", "--host", "0.0.0.0", "--forwarded-allow-ips", "*", "--proxy-headers"]
