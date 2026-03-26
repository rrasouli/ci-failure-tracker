FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install dependencies with specific secure versions
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /data

# Expose port
EXPOSE 8080

# Run gunicorn
CMD ["python3", "-m", "gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]
