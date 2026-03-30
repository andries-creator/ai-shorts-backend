FROM python:3.10-slim

# install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# upgrade pip tools first
RUN pip install --upgrade pip setuptools wheel

# install python packages
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# start server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
