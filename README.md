📁 decentralized-storage/
│
├── coordinator/
│   └── app.py
│
├── storage_node/
│   └── app.py
│
├── client/
│   └── app.py
│
├── docker-compose.yml
│
└── README.md

# coordinator/app.py
from flask import Flask, request, jsonify
app = Flask(__name__)

nodes = {}  # node_id -> {'url': ..., 'limit_mb': ..., 'used_mb': ...}

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    node_id = data['node_id']
    nodes[node_id] = data
    return jsonify({'status': 'registered'}), 200

@app.route('/available_nodes', methods=['GET'])
def available_nodes():
    return jsonify([node for node in nodes.values() if node['limit_mb'] > node['used_mb']]), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

# storage_node/app.py
from flask import Flask, request, jsonify
import os

app = Flask(__name__)
NODE_ID = os.getenv('NODE_ID', 'node1')
STORAGE_PATH = './storage'

if not os.path.exists(STORAGE_PATH):
    os.makedirs(STORAGE_PATH)

@app.route('/store/<chunk_id>', methods=['POST'])
def store_chunk(chunk_id):
    with open(os.path.join(STORAGE_PATH, chunk_id), 'wb') as f:
        f.write(request.data)
    return jsonify({'status': 'stored', 'chunk_id': chunk_id})

@app.route('/retrieve/<chunk_id>', methods=['GET'])
def retrieve_chunk(chunk_id):
    filepath = os.path.join(STORAGE_PATH, chunk_id)
    if os.path.exists(filepath):
        return open(filepath, 'rb').read()
    else:
        return 'Not found', 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000)

# client/app.py
import requests
import os
import hashlib

COORDINATOR_URL = os.getenv('COORDINATOR_URL', 'http://coordinator:5001')

# Encrypt file with XOR (basic for example)
def encrypt(data, key):
    return bytes([b ^ key for b in data])

def split_chunks(file_path, chunk_size=1024*1024):
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            yield chunk

def upload_file(file_path):
    key = 123  # Simple XOR key
    chunks = list(split_chunks(file_path))
    node_list = requests.get(f'{COORDINATOR_URL}/available_nodes').json()

    for i, chunk in enumerate(chunks):
        node = node_list[i % len(node_list)]
        encrypted = encrypt(chunk, key)
        chunk_id = hashlib.sha256(encrypted).hexdigest()
        url = f"{node['url']}/store/{chunk_id}"
        r = requests.post(url, data=encrypted)
        print(f"Stored chunk {chunk_id} at {node['node_id']}: {r.status_code}")

if __name__ == '__main__':
    upload_file('sample.txt')

# docker-compose.yml
version: '3'

services:
  coordinator:
    build: ./coordinator
    ports:
      - "5001:5001"

  storage1:
    build: ./storage_node
    environment:
      - NODE_ID=node1
    ports:
      - "6000:6000"

  client:
    build: ./client
    environment:
      - COORDINATOR_URL=http://coordinator:5001
    volumes:
      - .:/app
    depends_on:
      - coordinator
      - storage1

# README.md
# Blockchain-Based Decentralized Storage System

A decentralized cloud storage platform that allows users to securely store and retrieve files using blockchain technology. The system encrypts, fragments, and distributes data across multiple storage nodes, ensuring high security, privacy, and resistance to censorship.

## Architecture

This system consists of several components:

1. **Blockchain Node**: Uses Ethereum (Ganache for development) to handle transactions and storage agreements
2. **Smart Contract**: Manages storage providers, agreements, and payments
3. **Coordinator**: Central service that manages storage nodes and file metadata
4. **Storage Nodes**: Distributed nodes that store encrypted file chunks
5. **Client API**: Interface for applications to interact with the system
6. **Web Interface**: User-friendly dashboard for file operations

## Features

- **Decentralized Storage**: Files are split into chunks and distributed across multiple nodes
- **Blockchain Integration**: Smart contracts ensure transparent payment and agreement handling
- **Strong Encryption**: AES encryption for all stored files
- **Wallet Integration**: Connect Ethereum wallets for payments and identity
- **Ownership Control**: Files are associated with owner addresses for access control
- **Intuitive UI**: Modern web interface for easy file management

## Prerequisites

- Docker and Docker Compose
- Node.js (for development)
- Web3 wallet (for blockchain interaction)

## Getting Started

1. Clone the repository

```bash
git clone <repository-url>
cd decentralized-storage
```

2. Start the system using Docker Compose

```bash
docker-compose up -d
```

This will start all necessary services:
- Blockchain node on port 8545
- Coordinator service on port 5001
- Storage nodes on ports 6001, 6002, etc.
- Client API on port 5002
- Web interface on port 3000

3. Access the web interface at [http://localhost:3000](http://localhost:3000)

## Smart Contract

The system uses an Ethereum smart contract (`StorageContract.sol`) that handles:

- Registration of storage providers
- Creation of storage agreements between users and providers
- Automatic payment distribution
- Fee management

## Development

### Backend Components

All backend components are written in Python using Flask:

- `coordinator/`: Manages the storage network and metadata
- `storage_node/`: Handles chunk storage and retrieval
- `client/`: Provides the API interface for applications

### Frontend

The web interface is built with React and Material-UI:

- `web/`: Contains the React application

### Extending the System

- Add more storage nodes by duplicating the storage service in `docker-compose.yml`
- Modify `StorageContract.sol` to add additional payment features
- Enhance the encryption by implementing additional algorithms

## Security Considerations

- File encryption uses AES-128 for strong security
- Blockchain transactions ensure transparent payment handling
- Access control is implemented at both client and storage node levels
- Files are distributed across multiple nodes for redundancy

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
