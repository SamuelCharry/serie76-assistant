FROM python:3.12-slim@sha256:b18b261e1b4974b4f321451ad5251ded85abb22c2b8b262da527dda1d031ab30 AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt
COPY backend backend
COPY scripts scripts

FROM base AS backend
EXPOSE 8000
COPY docker/entrypoint.sh /app/docker/entrypoint.sh
ENTRYPOINT ["sh", "/app/docker/entrypoint.sh"]
