# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# Zero third-party pip dependencies - pure standard library
COPY . /app

# Non-root user and persistent database storage mount (Step 6.1)
RUN mkdir -p /app/data && \
    useradd -m -u 1000 cifuser && \
    chown -R cifuser:cifuser /app

VOLUME ["/app/data"]

ENV PORT=8080
ENV CIF_BIND=0.0.0.0
ENV CIF_DB_PATH=/app/data/context_intelligence.db
ENV PYTHONUNBUFFERED=1

USER cifuser

EXPOSE 8080

CMD ["python", "server.py"]
