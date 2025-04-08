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

app = Flask(__name__)
CORS(app)

NODE_ID = os.getenv('NODE_ID', 'node_default')
STORAGE_PATH = './storage'
STORAGE_LIMIT_MB = int(os.getenv('STORAGE_LIMIT_MB', '1024'))  # default 1GB
PRICE_PER_MB = int(os.getenv('PRICE_PER_MB', '1'))  # price in wei per MB per day

if not os.path.exists(STORAGE_PATH):
    os.makedirs(STORAGE_PATH)

COORDINATOR_URL = os.getenv('COORDINATOR_URL', 'http://coordinator:5001')
WALLET_ADDRESS = os.getenv('WALLET_ADDRESS', '')
WALLET_PRIVATE_KEY = os.getenv('WALLET_PRIVATE_KEY', '')

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

@app.route('/store/<chunk_id>', methods=['POST'])
def store_chunk(chunk_id):
    used = get_used_space_mb()
    if used >= STORAGE_LIMIT_MB:
        return jsonify({'error': 'Storage full'}), 507

    # Get optional metadata
    owner = request.headers.get('X-Owner', 'anonymous')
    file_id = request.headers.get('X-File-Id', '')
    encryption = request.headers.get('X-Encryption', 'none')
    
    # Store the chunk
    filepath = os.path.join(STORAGE_PATH, chunk_id)
    with open(filepath, 'wb') as f:
        f.write(request.data)
    
    # Update metadata
    chunk_size = len(request.data) / (1024 * 1024)  # Size in MB
    metadata = load_chunks_metadata()
    metadata[chunk_id] = {
        'chunk_id': chunk_id,
        'file_id': file_id,
        'owner': owner,
        'size_mb': chunk_size,
        'created_at': time.time(),
        'encryption': encryption
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
    filepath = os.path.join(STORAGE_PATH, chunk_id)
    if os.path.exists(filepath):
        return open(filepath, 'rb').read()
    else:
        return jsonify({'error': 'Chunk not found'}), 404

@app.route('/list_chunks', methods=['GET'])
def list_chunks():
    metadata = load_chunks_metadata()
    owner = request.args.get('owner')
    file_id = request.args.get('file_id')
    
    if owner:
        chunks = [data for _, data in metadata.items() if data.get('owner') == owner]
    elif file_id:
        chunks = [data for _, data in metadata.items() if data.get('file_id') == file_id]
    else:
        chunks = list(metadata.values())
    
    return jsonify(chunks), 200

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'node_id': NODE_ID,
        'used_mb': round(get_used_space_mb(), 2),
        'limit_mb': STORAGE_LIMIT_MB,
        'price_per_mb': PRICE_PER_MB,
        'wallet_address': WALLET_ADDRESS
    })

@app.route('/delete/<chunk_id>', methods=['DELETE'])
def delete_chunk(chunk_id):
    filepath = os.path.join(STORAGE_PATH, chunk_id)
    if os.path.exists(filepath):
        # Check authorization
        metadata = load_chunks_metadata()
        if chunk_id in metadata:
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
    res = requests.post(f'{COORDINATOR_URL}/register', json={
        'node_id': NODE_ID,
        'url': f'http://{os.getenv("HOSTNAME", "localhost")}:6000',
        'limit_mb': STORAGE_LIMIT_MB,
        'used_mb': used,
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
