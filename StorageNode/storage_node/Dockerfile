FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create storage directory
RUN mkdir -p ./storage

# Copy application code
COPY . .

# Expose the port the app runs on
EXPOSE 6000

# Command to run the application
CMD ["python", "app.py"] 