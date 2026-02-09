# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory if it doesn't exist
RUN mkdir -p data

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV ENV=prod

# Run the application (production mode, no reload)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
