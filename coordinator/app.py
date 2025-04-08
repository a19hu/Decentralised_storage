from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
from web3 import Web3
import requests

app = Flask(__name__)
CORS(app)

# Configure blockchain connection
BLOCKCHAIN_URL = os.getenv('BLOCKCHAIN_URL', 'http://blockchain:8545')
web3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_URL))

# Load smart contract ABI and address
CONTRACT_ABI_PATH = os.path.join(os.path.dirname(__file__), 'contract_abi.json')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS', '')

# Ensure data directory exists
DATA_DIR = './data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# JSON file to store file metadata
METADATA_FILE = os.path.join(DATA_DIR, 'file_metadata.json')

# Initialize metadata storage
if not os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, 'w') as f:
        json.dump({}, f)

# Load contract if available
contract = None
if os.path.exists(CONTRACT_ABI_PATH) and CONTRACT_ADDRESS:
    with open(CONTRACT_ABI_PATH, 'r') as f:
        contract_abi = json.load(f)
    contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

# Registered storage nodes
# Format: node_id -> {'url': ..., 'limit_mb': ..., 'used_mb': ...}
nodes = {}

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    node_id = data.get('node_id')
    url = data.get('url')
    limit_mb = data.get('limit_mb')
    used_mb = data.get('used_mb')

    if not node_id or not url:
        return jsonify({'error': 'Missing node_id or url'}), 400

    nodes[node_id] = {
        'node_id': node_id,
        'url': url,
        'limit_mb': limit_mb,
        'used_mb': used_mb
    }

    return jsonify({'status': 'registered', 'node_id': node_id}), 200

@app.route('/available_nodes', methods=['GET'])
def available_nodes():
    return jsonify([
        node for node in nodes.values()
        if node.get('used_mb', 0) < node.get('limit_mb', 0)
    ]), 200

@app.route('/all_nodes', methods=['GET'])
def all_nodes():
    return jsonify(list(nodes.values())), 200

@app.route('/store_file_metadata', methods=['POST'])
def store_file_metadata():
    data = request.json
    file_id = data.get('file_id')
    filename = data.get('filename')
    size = data.get('size')
    owner = data.get('owner')
    chunks = data.get('chunks')
    
    if not all([file_id, filename, chunks]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Load current metadata
    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)
    
    # Store new file metadata
    metadata[file_id] = {
        'file_id': file_id,
        'filename': filename,
        'size': size,
        'owner': owner,
        'chunks': chunks,
        'created_at': data.get('created_at')
    }
    
    # Save updated metadata
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f)
    
    return jsonify({'status': 'stored', 'file_id': file_id}), 200

@app.route('/get_file_metadata/<file_id>', methods=['GET'])
def get_file_metadata(file_id):
    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)
    
    if file_id in metadata:
        return jsonify(metadata[file_id]), 200
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/list_files', methods=['GET'])
def list_files():
    owner = request.args.get('owner')
    
    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)
    
    if owner:
        files = [data for _, data in metadata.items() if data.get('owner') == owner]
    else:
        files = list(metadata.values())
    
    return jsonify(files), 200

@app.route('/save_contract_abi', methods=['POST'])
def save_contract_abi():
    """Save the contract ABI and address for later use"""
    data = request.json
    contract_abi = data.get('abi')
    contract_address = data.get('address')
    
    if not contract_abi or not contract_address:
        return jsonify({'error': 'Missing ABI or address'}), 400
    
    # Save ABI to file
    with open(CONTRACT_ABI_PATH, 'w') as f:
        json.dump(contract_abi, f)
    
    # Store address in environment
    os.environ['CONTRACT_ADDRESS'] = contract_address
    
    # Initialize contract
    global contract
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)
    
    return jsonify({'status': 'success'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
