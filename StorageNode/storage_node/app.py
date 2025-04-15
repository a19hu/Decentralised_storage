from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import json
import time
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import shutil
import stat
from web3 import Web3

app = Flask(__name__)
CORS(app)

NODE_ID = os.getenv('NODE_ID', 'node_default')
STORAGE_PATH = './storage'
LOCKED_STORAGE_PATH = './locked_storage'  # Directory for storage that is locked for rental
STORAGE_LIMIT_MB = int(os.getenv('STORAGE_LIMIT_MB', '1024'))  # default 1GB
PRICE_PER_MB = int(os.getenv('PRICE_PER_MB', '1'))  # price in wei per MB per day

# Create storage directories if they don't exist
if not os.path.exists(STORAGE_PATH):
    os.makedirs(STORAGE_PATH)

if not os.path.exists(LOCKED_STORAGE_PATH):
    os.makedirs(LOCKED_STORAGE_PATH)

COORDINATOR_URL = os.getenv('COORDINATOR_URL', 'http://coordinator:5001')
BLOCKCHAIN_URL = os.getenv('BLOCKCHAIN_URL', 'http://blockchain:8545')
WALLET_ADDRESS = os.getenv('WALLET_ADDRESS', '')
WALLET_PRIVATE_KEY = os.getenv('WALLET_PRIVATE_KEY', '')

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_URL))

# Load contract if ABI is available
CONTRACT_ABI_PATH = os.path.join(os.path.dirname(__file__), 'data', 'contract_abi.json')
CONTRACT_ADDRESS_FILE = os.getenv('CONTRACT_ADDRESS_FILE', '/app/data/contract_address.txt')
contract = None
CONTRACT_ADDRESS = ''

# Create data directory if it doesn't exist
os.makedirs(os.path.dirname(CONTRACT_ABI_PATH), exist_ok=True)

# Read contract address from file if it exists
if os.path.exists(CONTRACT_ADDRESS_FILE):
    try:
        with open(CONTRACT_ADDRESS_FILE, 'r') as f:
            CONTRACT_ADDRESS = f.read().strip()
        print(f"Loaded contract address: {CONTRACT_ADDRESS}")
    except Exception as e:
        print(f"Error reading contract address: {e}")

# Copy contract ABI from coordinator if not available
if not os.path.exists(CONTRACT_ABI_PATH) and CONTRACT_ADDRESS:
    try:
        coordinator_abi_path = '/app/data/contract_abi.json'
        if os.path.exists(coordinator_abi_path):
            shutil.copy(coordinator_abi_path, CONTRACT_ABI_PATH)
            print(f"Copied contract ABI from coordinator")
    except Exception as e:
        print(f"Error copying contract ABI: {e}")

# Load contract ABI if available
if os.path.exists(CONTRACT_ABI_PATH) and CONTRACT_ADDRESS:
    try:
        with open(CONTRACT_ABI_PATH, 'r') as f:
            contract_abi = json.load(f)
        contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)
        print(f"Contract loaded successfully at address {CONTRACT_ADDRESS}")
    except Exception as e:
        print(f"Error loading contract: {e}")

# Store file chunk metadata
CHUNKS_METADATA_FILE = 'chunks_metadata.json'
if not os.path.exists(CHUNKS_METADATA_FILE):
    with open(CHUNKS_METADATA_FILE, 'w') as f:
        json.dump({}, f)

def load_chunks_metadata():
    try:
        with open(CHUNKS_METADATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_chunks_metadata(metadata):
    with open(CHUNKS_METADATA_FILE, 'w') as f:
        json.dump(metadata, f)

# Get used storage in MB
def get_used_space_mb():
    total = 0
    for f in os.listdir(STORAGE_PATH):
        total += os.path.getsize(os.path.join(STORAGE_PATH, f))
    return total / (1024 * 1024)

# Get locked storage space in MB
def get_locked_space_mb():
    total = 0
    for f in os.listdir(LOCKED_STORAGE_PATH):
        total += os.path.getsize(os.path.join(LOCKED_STORAGE_PATH, f))
    return total / (1024 * 1024)

# Lock storage space for client usage
@app.route('/lock_storage', methods=['POST'])
def lock_storage():
    size_mb = int(request.json.get('size_mb', 0))
    
    if size_mb <= 0:
        return jsonify({'error': 'Size must be greater than 0'}), 400
    
    # Check if enough free space is available
    available = STORAGE_LIMIT_MB - get_used_space_mb() - get_locked_space_mb()
    if available < size_mb:
        return jsonify({'error': f'Not enough free space. Available: {available}MB, Requested: {size_mb}MB'}), 400
    
    # Create a dedicated space file of specified size (sparse file)
    lock_file = os.path.join(LOCKED_STORAGE_PATH, f"{NODE_ID}_{size_mb}MB.space")
    
    # Create a sparse file of the specified size
    with open(lock_file, 'wb') as f:
        f.seek(size_mb * 1024 * 1024 - 1)  # Convert MB to bytes
        f.write(b'\0')
    
    # Set file permissions to prevent modification (readonly except for owner)
    os.chmod(lock_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    
    # Register the locked storage with the blockchain
    if contract:
        try:
            tx_hash = contract.functions.lockStorage(
                NODE_ID,
                size_mb
            ).transact({'from': WALLET_ADDRESS})
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            tx_success = tx_receipt.status == 1
        except Exception as e:
            return jsonify({'error': f'Blockchain transaction failed: {str(e)}'}), 500
    
    # Update coordinator
    try:
        update_used_space()
    except Exception as e:
        return jsonify({'error': f'Failed to update coordinator: {str(e)}'}), 500
    
    return jsonify({
        'status': 'locked',
        'node_id': NODE_ID,
        'size_mb': size_mb,
        'lock_file': lock_file
    }), 200

@app.route('/store/<chunk_id>', methods=['POST'])
def store_chunk(chunk_id):
    used = get_used_space_mb()
    if used >= STORAGE_LIMIT_MB:
        return jsonify({'error': 'Storage full'}), 507

    # Get optional metadata
    owner = request.headers.get('X-Owner', 'anonymous')
    file_id = request.headers.get('X-File-Id', '')
    encryption = request.headers.get('X-Encryption', 'none')
    agreement_id = request.headers.get('X-Agreement-Id', '')
    
    # If this is for a locked storage, store it in the appropriate directory
    target_dir = STORAGE_PATH
    if agreement_id:
        target_dir = LOCKED_STORAGE_PATH
    
    # Store the chunk
    filepath = os.path.join(target_dir, chunk_id)
    with open(filepath, 'wb') as f:
        f.write(request.data)
    
    # Set permissions so it's secure and immutable by seller
    if agreement_id:
        # Make it readable by owner but not writable by anyone
        os.chmod(filepath, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    
    # Update metadata
    chunk_size = len(request.data) / (1024 * 1024)  # Size in MB
    metadata = load_chunks_metadata()
    metadata[chunk_id] = {
        'chunk_id': chunk_id,
        'file_id': file_id,
        'owner': owner,
        'size_mb': chunk_size,
        'created_at': time.time(),
        'encryption': encryption,
        'agreement_id': agreement_id,
        'in_locked_storage': bool(agreement_id)
    }
    save_chunks_metadata(metadata)
    
    # Register the updated space usage with coordinator
    try:
        update_used_space()
    except:
        pass  # Silent failure if coordinator is unavailable
    
    return jsonify({
        'status': 'stored', 
        'chunk_id': chunk_id,
        'node_id': NODE_ID
    })

@app.route('/retrieve/<chunk_id>', methods=['GET'])
def retrieve_chunk(chunk_id):
    # Check main storage path
    filepath = os.path.join(STORAGE_PATH, chunk_id)
    
    # If not in main storage, check locked storage
    if not os.path.exists(filepath):
        filepath = os.path.join(LOCKED_STORAGE_PATH, chunk_id)
    
    if os.path.exists(filepath):
        # Check if this requires authorization (for locked storage)
        metadata = load_chunks_metadata()
        if chunk_id in metadata and metadata[chunk_id].get('in_locked_storage', False):
            # Require owner verification or agreement verification
            owner = request.headers.get('X-Owner')
            agreement_id = request.headers.get('X-Agreement-Id')
            
            if not owner and not agreement_id:
                return jsonify({'error': 'Authorization required for this chunk'}), 403
            
            # If using agreement_id, verify with blockchain
            if agreement_id and contract:
                try:
                    # Verify access is allowed - this would be a call to the contract
                    # to check if the requester is the owner of the agreement
                    pass  # Additional blockchain verification would go here
                except:
                    return jsonify({'error': 'Blockchain verification failed'}), 403
            
            # If using owner, check against metadata
            if owner and metadata[chunk_id].get('owner') != owner:
                return jsonify({'error': 'Owner mismatch'}), 403
        
        return open(filepath, 'rb').read()
    else:
        return jsonify({'error': 'Chunk not found'}), 404

@app.route('/list_chunks', methods=['GET'])
def list_chunks():
    metadata = load_chunks_metadata()
    owner = request.args.get('owner')
    file_id = request.args.get('file_id')
    agreement_id = request.args.get('agreement_id')
    
    # Filter results
    if owner:
        chunks = [data for _, data in metadata.items() if data.get('owner') == owner]
    elif file_id:
        chunks = [data for _, data in metadata.items() if data.get('file_id') == file_id]
    elif agreement_id:
        chunks = [data for _, data in metadata.items() if data.get('agreement_id') == agreement_id]
    else:
        # If no filter, only return non-locked storage chunks
        chunks = [data for _, data in metadata.items() if not data.get('in_locked_storage', False)]
    
    return jsonify(chunks), 200

@app.route('/status', methods=['GET'])
def status():
    locked_mb = get_locked_space_mb()
    used_mb = get_used_space_mb()
    
    return jsonify({
        'node_id': NODE_ID,
        'used_mb': round(used_mb, 2),
        'locked_mb': round(locked_mb, 2),
        'total_used_mb': round(used_mb + locked_mb, 2),
        'limit_mb': STORAGE_LIMIT_MB,
        'available_mb': round(STORAGE_LIMIT_MB - used_mb - locked_mb, 2),
        'price_per_mb': PRICE_PER_MB,
        'wallet_address': WALLET_ADDRESS
    })

@app.route('/delete/<chunk_id>', methods=['DELETE'])
def delete_chunk(chunk_id):
    # Check main storage path
    filepath = os.path.join(STORAGE_PATH, chunk_id)
    
    # If not in main storage, check locked storage
    if not os.path.exists(filepath):
        filepath = os.path.join(LOCKED_STORAGE_PATH, chunk_id)
    
    if os.path.exists(filepath):
        # Check authorization
        metadata = load_chunks_metadata()
        if chunk_id in metadata:
            # For locked storage, require specific authorization
            if metadata[chunk_id].get('in_locked_storage', False):
                # Only allow deletion by the owner or via agreement ID
                owner = request.headers.get('X-Owner')
                agreement_id = request.headers.get('X-Agreement-Id')
                
                if not owner and not agreement_id:
                    return jsonify({'error': 'Authorization required for this chunk'}), 403
                
                # Verify with metadata
                chunk_owner = metadata[chunk_id].get('owner')
                chunk_agreement = metadata[chunk_id].get('agreement_id')
                
                if (owner and chunk_owner != owner) or (agreement_id and chunk_agreement != agreement_id):
                    return jsonify({'error': 'Not authorized to delete this chunk'}), 403
            else:
                # For regular storage
                owner = metadata[chunk_id].get('owner')
                req_owner = request.headers.get('X-Owner')
                if owner != 'anonymous' and owner != req_owner:
                    return jsonify({'error': 'Unauthorized'}), 403
            
            # Delete the file
            os.remove(filepath)
            
            # Update metadata
            del metadata[chunk_id]
            save_chunks_metadata(metadata)
            
            # Update coordinator
            try:
                update_used_space()
            except:
                pass
            
            return jsonify({'status': 'deleted'})
        else:
            return jsonify({'error': 'Chunk metadata not found'}), 404
    else:
        return jsonify({'error': 'Chunk not found'}), 404

def update_used_space():
    """Update the coordinator with current used space"""
    used = get_used_space_mb()
    locked = get_locked_space_mb()
    
    # Get the host IP from environment variable or use localhost
    host_ip = os.getenv('HOST_IP', 'localhost')
    port = os.getenv('PORT', '6000')
    
    res = requests.post(f'{COORDINATOR_URL}/register', json={
        'node_id': NODE_ID,
        'url': f'http://{host_ip}:{port}',
        'limit_mb': STORAGE_LIMIT_MB,
        'used_mb': used,
        'locked_mb': locked,
        'price_per_mb': PRICE_PER_MB,
        'wallet_address': WALLET_ADDRESS
    })
    return res.json()

def register_with_coordinator():
    """Initial registration with the coordinator"""
    try:
        update_used_space()
        print('Registered with coordinator')
    except Exception as e:
        print('Coordinator registration failed:', e)

if __name__ == '__main__':
    register_with_coordinator()
    app.run(host='0.0.0.0', port=6000)
