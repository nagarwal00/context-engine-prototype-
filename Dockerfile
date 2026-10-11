# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# Zero third-party pip dependencies - pure standard library
COPY . /app

ENV PORT=8080
ENV CIF_BIND=0.0.0.0
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["python", "server.py"]
