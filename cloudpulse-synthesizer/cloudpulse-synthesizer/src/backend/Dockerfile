FROM python:3.12-slim

WORKDIR /app

# Upgrade pip first to ensure compatibility with modern wheels
RUN pip install --no-cache-dir --upgrade pip

# Copy requirements from root context
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY . .

EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]