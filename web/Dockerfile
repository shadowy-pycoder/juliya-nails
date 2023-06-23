FROM python:3.10.10-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc
RUN apt-get install -y --fix-missing curl

RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

FROM python:3.10.10-slim

RUN groupadd -g 999 python && useradd -r -u 999 -g python python

RUN mkdir /app && chown python:python /app
WORKDIR /app

COPY --chown=python:python --from=builder /app/venv ./venv
COPY --chown=python:python . .
COPY --chown=python:python boot.sh .

USER 999

ENV PATH="/app/venv/bin:$PATH"

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--access-logfile", "-", "--error-logfile", "-", "-w", "3", "run:app"]