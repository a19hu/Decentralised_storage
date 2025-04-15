# Blockchain-Based Decentralized Storage System

A decentralized cloud storage platform that allows users to securely store and retrieve files using blockchain technology. The system encrypts, fragments, and distributes data across multiple storage nodes, ensuring high security, privacy, and resistance to censorship.

## Features

### Core Features
- **Decentralized Storage**: Files are split into chunks and distributed across multiple nodes
- **Blockchain Integration**: Smart contracts ensure transparent payment and agreement handling
- **Strong Encryption**: AES encryption for all stored files
- **Wallet Integration**: Connect Ethereum wallets for payments and identity
- **Ownership Control**: Files are associated with owner addresses for access control

### Advanced Capabilities
- **Efficient Search**: Utilizes B-trees for metadata retrieval (30% faster search)
- **Reward System**: Users earn tokens for contributing storage space
- **Distributed Storage**: IPFS integration for decentralized file storage
- **Dataset Marketplace**: Optional module for buying/selling datasets

## Tech Stack
- **Frontend**: React.js with Material-UI
- **Backend**: Python (Flask)
- **Blockchain**: Ethereum (Ganache for development)
- **Database**: MongoDB
- **Distributed Storage**: IPFS + Custom storage nodes
- **Indexing**: B-trees for efficient search

## File Structure
decentralized-storage/
├── server/
│ ├── client/
│ ├──├── app.py
│ ├──├── Dockerfile
│ ├──├── requirements.txt
│ ├── contract-deployer/
│ ├──├── deplot_contract.py
│ ├──├── Dockerfile
│ ├──├── StorageControl.sol
│ ├── cordinator/
│ ├──├── data
│ ├──├── app.py
│ ├──├── Dockerfile
│ ├──├── requirements.txt
│ ├── web/
│ ├──├── public
│ ├──├── src
│ ├──├── Dockerfile
│ ├── docker-compose.yml
├── StorageNode/
│ ├── storage_node/
│ ├──├── app.py
│ ├──├── Dockerfile
│ ├──├── requirements.txt
| ├── docker-compose.yml
├── .gitignore
└── README.md


## Prerequisites

- Docker and Docker Compose
- Node.js (v16+) for development
- Python 3.8+
- Web3 wallet (MetaMask recommended)
- MongoDB (local or cloud instance)

## Installation & Running

### Quick Start with Docker
```bash
git clone <repository-url>
cd decentralized-storage
docker-compose up -d
```

This will start:
Blockchain node on port 8545
Coordinator service on port 5001
Storage nodes on ports 6001, 6002
Client API on port 5002
Web interface on port 3000
Access the web interface at: http://localhost:3000

### Manual Setup (Development)
**Set up environment:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Configure environment variables:**
Create .env file:
```bash
MONGO_URI=mongodb://localhost:27017
ETHEREUM_NODE=http://localhost:8545
CONTRACT_ADDRESS=0xYourContractAddress
IPFS_API=/ip4/127.0.0.1/tcp/5001
```

**Start services:**
```bash
python coordinator/app.py
python storage_node/app.py --port 6001
python storage_node/app.py --port 6002
python client/app.py
cd web
npm install
npm start
```

## Storage Contract Details

The `StorageContract.sol` handles:
- **Storage provider registration**  
  New nodes can register to become storage providers
- **Storage agreements**  
  Creates binding agreements between users and storage providers
- **Automatic payment distribution**  
  Handles escrow and payment release upon successful storage
- **Fee management**  
  Manages platform fees and reward distributions


## Usage Guide
### Connect Wallet
1. Click **"Connect Wallet"** in the web interface  
2. Approve connection in your wallet (MetaMask recommended)  

### Upload Files
1. Select files through the interface  
2. Files are automatically processed:  
   - 🔒 Encrypted (AES-128)  
   - ✂️ Fragmented into chunks  
   - 🌐 Distributed across storage nodes  

### File Management
- 📁 View/delete uploaded files  
- 📝 Monitor active storage agreements  
- 💰 Check payment status and history  

### Become a Storage Provider
1. Register as a storage provider in the "Providers" section  
2. Earn tokens for storing file chunks  
3. Set your custom storage terms:  
   - 💵 Pricing per GB  
   - ⏳ Minimum storage duration  
   - 📦 Available storage capacity  

> ℹ️ All transactions are recorded on the Ethereum blockchain for transparency.

## Contributing

We welcome contributions from the community! Here's how to get started:
1. **Fork the Repository**  
   Click the "Fork" button at the top-right of the repository page
2. **Create a Feature Branch**  
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make Your Changes**
4. **Commit Your Changes** 
   ```bash
   git commit -m "feat: add your feature description"
   ```
5. **Push to Your Branch**
   ```bash
   git push origin feature/your-feature-name
   ```
6. **Submit a Pull Request**
