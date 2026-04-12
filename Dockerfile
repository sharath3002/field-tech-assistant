FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Install minimal deps (reduce network + build issues)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

ENV PORT=7860

# Run FastAPI server
CMD ["python", "server/app.py"]


