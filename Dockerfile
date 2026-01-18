FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends \
    libxcb1 \
    libgl1 \
    libx11-6 \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

COPY ./app ./app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:start_application", "--factory", "--host", "0.0.0.0", "--port", "8000"]