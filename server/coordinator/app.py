from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import requests
from web3 import Web3
app = Flask(__name__)
CORS(app)

CONTRACT_ABI_PATH ='./data/contract_abi.json'
CONTRACT_ADDRESS_FILE ='./data/contract_address.txt'

DATA_DIR = './data'

METADATA_FILE = os.path.join(DATA_DIR, 'file_metadata.json')
AGREEMENTS_FILE = os.path.join(DATA_DIR, 'agreements_metadata.json')

BLOCKCHAIN_URL = os.getenv('BLOCKCHAIN_URL', 'http://localhost:8545')  # Default to localhost if not set
web3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_URL))

if not os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, 'w') as f:
        json.dump({}, f)

if not os.path.exists(AGREEMENTS_FILE):
    with open(AGREEMENTS_FILE, 'w') as f:
        json.dump({}, f)

contract = None
CONTRACT_ADDRESS = ''

if os.path.exists(CONTRACT_ADDRESS_FILE):
    try:
        with open(CONTRACT_ADDRESS_FILE, 'r') as f:
            CONTRACT_ADDRESS = f.read().strip()
        print(f"Loaded contract address: {CONTRACT_ADDRESS}")
    except Exception as e:
        print(f"Error reading contract address: {e}")

if os.path.exists(CONTRACT_ABI_PATH):
    try:
        with open(CONTRACT_ABI_PATH, 'r') as f:
            contract_abi = json.load(f)
        contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)
        print(f"Contract loaded successfully at address {CONTRACT_ADDRESS}")
    except Exception as e:
        print(f"Error loading contract: {e}")

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
    locked_mb = data.get('locked_mb', 100)
    price_per_mb = data.get('price_per_mb', 1)
    wallet_address = data.get('wallet_address', '')

    if not node_id or not url:
        return jsonify({'error': 'Missing node_id or url'}), 400

    nodes[node_id] = {
        'node_id': node_id,
        'url': url,
        'limit_mb': limit_mb,
        'used_mb': used_mb,
        'locked_mb': locked_mb,
        'price_per_mb': price_per_mb,
        'wallet_address': wallet_address
    }

    return jsonify({'status': 'registered', 'node_id': node_id}), 200

@app.route('/deregister', methods=['POST'])
def deregister():
    data = request.json
    node_id = data.get('node_id')
    
    if not node_id:
        return jsonify({'error': 'Missing node_id'}), 400
    
    if node_id in nodes:
        del nodes[node_id]
        return jsonify({'status': 'deregistered', 'node_id': node_id}), 200
    else:
        return jsonify({'error': 'Node not found', 'node_id': node_id}), 404

@app.route('/available_nodes', methods=['GET'])
def available_nodes():
    # Show nodes that have available space (either regular or locked)
    return jsonify([
        node for node in nodes.values()
        if node.get('used_mb', 0) < node.get('limit_mb', 0) or node.get('locked_mb', 0) > 0
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
    agreement_id = data.get('agreement_id')
    
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
        'created_at': data.get('created_at'),
        'encryption': data.get('encryption', 'none'),
        'agreement_id': agreement_id
    }
    
    # If this is for an agreement, store the key
    if 'key' in data:
        metadata[file_id]['key'] = data['key']
    
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
    agreement_id = request.args.get('agreement_id')
    
    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)
    
    if owner:
        files = [data for _, data in metadata.items() if data.get('owner') == owner]
    elif agreement_id:
        files = [data for _, data in metadata.items() if data.get('agreement_id') == agreement_id]
    else:
        files = list(metadata.values())
    
    return jsonify(files), 200

@app.route('/delete_file_metadata/<file_id>', methods=['DELETE'])
def delete_file_metadata(file_id):
    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)
    
    if file_id not in metadata:
        return jsonify({'error': 'File not found'}), 404
    
    # Verify ownership
    owner = request.headers.get('X-Owner')
    if metadata[file_id]['owner'] != 'anonymous' and metadata[file_id]['owner'] != owner:
        return jsonify({'error': 'Not authorized to delete this file'}), 403
    
    # Remove file metadata
    del metadata[file_id]
    
    # Save updated metadata
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f)
    
    return jsonify({'status': 'deleted', 'file_id': file_id}), 200

@app.route('/storage_agreements', methods=['GET'])
def storage_agreements():
    """List all storage agreements"""
    if not contract:
        return jsonify({'error': 'Smart contract not available'}), 500
    
    # Load agreements from local storage
    with open(AGREEMENTS_FILE, 'r') as f:
        agreements = json.load(f)
    
    return jsonify(list(agreements.values())), 200

@app.route('/sync_agreements', methods=['POST'])
def sync_agreements():
    """Sync blockchain agreements with local storage"""
    if not contract:
        return jsonify({'error': 'Smart contract not available'}), 500
    
    # For each node, get provider agreements from blockchain
    updated_agreements = {}
    
    for node_id, node in nodes.items():
        if 'wallet_address' in node and node['wallet_address']:
            try:
                # Get provider agreements
                provider_agreements = contract.functions.getProviderAgreements(node_id).call({
                    'from': node['wallet_address']
                })
                
                for agreement in provider_agreements:
                    agreement_id = f"{agreement[1]}-{agreement[2]}"  # node_id-sizeInMB
                    updated_agreements[agreement_id] = {
                        'agreement_id': agreement_id,
                        'user': agreement[0],
                        'node_id': agreement[1],
                        'size_mb': agreement[2],
                        'duration_days': agreement[3],
                        'total_price': agreement[4],
                        'start_time': agreement[5],
                        'active': agreement[6]
                    }
            except Exception as e:
                print(f"Error getting agreements for {node_id}: {e}")
    
    # Save updated agreements
    with open(AGREEMENTS_FILE, 'w') as f:
        json.dump(updated_agreements, f)
    
    return jsonify({
        'status': 'synced',
        'agreements_count': len(updated_agreements)
    }), 200

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
