FROM python:3.12-slim@sha256:b18b261e1b4974b4f321451ad5251ded85abb22c2b8b262da527dda1d031ab30 AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt requirements-backend.lock.txt requirements-conversation.lock.txt ./
RUN pip install --no-cache-dir -r requirements-backend.lock.txt -r requirements-conversation.lock.txt
COPY backend backend
COPY scripts scripts

FROM base AS ocr
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng && rm -rf /var/lib/apt/lists/*
ENTRYPOINT ["python", "scripts/ocr_probe.py"]

FROM base AS backend
EXPOSE 8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
