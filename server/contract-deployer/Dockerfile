FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy contract deployment script and contract
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir web3 py-solc-x

# Create data directory
RUN mkdir -p /app/data

# Command to run the deployment script
CMD ["python", "deploy_contract.py"] 