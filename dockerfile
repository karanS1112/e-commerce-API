
# Python ka lightweight base image use karenge
FROM python:3.12-slim

# Container ke andar working directory
WORKDIR /app

# Python ko .pyc files aur output buffering se bachane ke liye
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Pehle dependencies copy karte hain, taaki Docker cache use kar sake
COPY requirements.txt .

# Project ki Python dependencies install karo
RUN pip install --no-cache-dir -r requirements.txt

# Application aur Alembic files container mein copy karo
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

# FastAPI app run karo
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
