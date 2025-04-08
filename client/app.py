from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import os
import hashlib
import time
import json
import uuid
import tempfile
from web3 import Web3
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64

app = Flask(__name__)
CORS(app)

COORDINATOR_URL = os.getenv('COORDINATOR_URL', 'http://coordinator:5001')
BLOCKCHAIN_URL = os.getenv('BLOCKCHAIN_URL', 'http://blockchain:8545')
TEMP_DIR = './temp'

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_URL))

# Load contract if ABI is available
CONTRACT_ABI_PATH = 'contract_abi.json'
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS', '')
contract = None

if os.path.exists(CONTRACT_ABI_PATH) and CONTRACT_ADDRESS:
    with open(CONTRACT_ABI_PATH, 'r') as f:
        contract_abi = json.load(f)
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

def generate_encryption_key():
    """Generate a random AES key"""
    return get_random_bytes(16)  # 128-bit key

def encrypt_data(data, key):
    """Encrypt data using AES"""
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data, AES.block_size))
    iv = base64.b64encode(cipher.iv).decode('utf-8')
    ct = base64.b64encode(ct_bytes).decode('utf-8')
    return json.dumps({'iv': iv, 'ciphertext': ct})

def decrypt_data(encrypted_data, key):
    """Decrypt AES encrypted data"""
    b64 = json.loads(encrypted_data)
    iv = base64.b64decode(b64['iv'])
    ct = base64.b64decode(b64['ciphertext'])
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), AES.block_size)
    return pt

def split_file_into_chunks(file_path, chunk_size=1024*1024):
    """Split a file into fixed-size chunks and return list of chunks"""
    chunks = []
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            chunks.append(chunk)
    return chunks

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file in request'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Get optional parameters
    owner = request.form.get('owner', 'anonymous')
    encryption = request.form.get('encryption', 'aes')
    
    # Save file temporarily
    temp_path = os.path.join(TEMP_DIR, file.filename)
    file.save(temp_path)
    
    # Generate a file ID
    file_id = str(uuid.uuid4())
    
    # Get storage nodes
    node_list_response = requests.get(f'{COORDINATOR_URL}/available_nodes')
    if node_list_response.status_code != 200:
        return jsonify({'error': 'Failed to get available storage nodes'}), 500
    
    node_list = node_list_response.json()
    if not node_list:
        return jsonify({'error': 'No storage nodes available'}), 503
    
    # Generate encryption key if needed
    key = None
    if encryption == 'aes':
        key = generate_encryption_key()
    
    # Split file into chunks
    chunks = split_file_into_chunks(temp_path)
    file_size = os.path.getsize(temp_path)
    
    # Upload each chunk to storage nodes
    chunk_metadata = []
    for i, chunk_data in enumerate(chunks):
        # Select a node using round-robin
        node = node_list[i % len(node_list)]
        
        # Encrypt chunk if required
        if encryption == 'aes' and key:
            # Convert chunk to JSON string for encryption
            encrypted_data = encrypt_data(chunk_data, key)
            chunk_data = encrypted_data.encode('utf-8')
            encryption_type = 'aes'
        else:
            encryption_type = 'none'
        
        # Generate chunk ID
        chunk_id = hashlib.sha256(chunk_data).hexdigest()
        
        # Upload to node
        headers = {
            'X-Owner': owner,
            'X-File-Id': file_id,
            'X-Encryption': encryption_type
        }
        url = f"{node['url']}/store/{chunk_id}"
        
        try:
            response = requests.post(url, data=chunk_data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                chunk_metadata.append({
                    'chunk_id': chunk_id,
                    'node_id': result['node_id'],
                    'node_url': node['url'],
                    'size': len(chunk_data),
                    'index': i,
                    'encryption': encryption_type
                })
            else:
                return jsonify({'error': f'Failed to upload chunk {i} to node {node["node_id"]}'}), 500
        except Exception as e:
            return jsonify({'error': f'Error uploading chunk {i}: {str(e)}'}), 500
    
    # Save file metadata to coordinator
    metadata = {
        'file_id': file_id,
        'filename': file.filename,
        'size': file_size,
        'chunks': chunk_metadata,
        'owner': owner,
        'created_at': time.time(),
        'encryption': encryption
    }
    
    # Store the encryption key if used
    if key:
        metadata['key'] = base64.b64encode(key).decode('utf-8')
    
    response = requests.post(f'{COORDINATOR_URL}/store_file_metadata', json=metadata)
    if response.status_code != 200:
        return jsonify({'error': 'Failed to store file metadata'}), 500
    
    # Cleanup temp file
    os.remove(temp_path)
    
    return jsonify({
        'status': 'success',
        'file_id': file_id,
        'size': file_size,
        'chunks': len(chunk_metadata)
    }), 200

@app.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    # Get file metadata
    response = requests.get(f'{COORDINATOR_URL}/get_file_metadata/{file_id}')
    if response.status_code != 200:
        return jsonify({'error': 'File not found'}), 404
    
    metadata = response.json()
    filename = metadata['filename']
    chunks = metadata['chunks']
    encryption = metadata.get('encryption', 'none')
    
    # Sort chunks by index
    chunks.sort(key=lambda x: x['index'])
    
    # Create temp file to assemble the chunks
    temp_file = os.path.join(TEMP_DIR, filename)
    
    with open(temp_file, 'wb') as f:
        for chunk in chunks:
            chunk_id = chunk['chunk_id']
            node_url = chunk['node_url']
            
            # Download chunk
            url = f"{node_url}/retrieve/{chunk_id}"
            response = requests.get(url)
            
            if response.status_code != 200:
                return jsonify({'error': f'Failed to download chunk {chunk_id}'}), 500
            
            chunk_data = response.content
            
            # Decrypt if needed
            if encryption == 'aes' and 'key' in metadata:
                key = base64.b64decode(metadata['key'])
                try:
                    # Chunk data is a JSON string
                    encrypted_data = chunk_data.decode('utf-8')
                    decrypted_data = decrypt_data(encrypted_data, key)
                    chunk_data = decrypted_data
                except Exception as e:
                    return jsonify({'error': f'Failed to decrypt chunk: {str(e)}'}), 500
            
            # Write chunk to file
            f.write(chunk_data)
    
    # Send the file
    return send_file(temp_file, as_attachment=True, download_name=filename)

@app.route('/list_files', methods=['GET'])
def list_files():
    # Get optional owner parameter
    owner = request.args.get('owner')
    
    # Call coordinator to list files
    url = f'{COORDINATOR_URL}/list_files'
    if owner:
        url += f'?owner={owner}'
    
    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({'error': 'Failed to list files'}), 500
    
    files = response.json()
    
    # Remove sensitive info like encryption keys
    for file in files:
        if 'key' in file:
            del file['key']
    
    return jsonify(files), 200

@app.route('/delete/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    # Get file metadata
    response = requests.get(f'{COORDINATOR_URL}/get_file_metadata/{file_id}')
    if response.status_code != 200:
        return jsonify({'error': 'File not found'}), 404
    
    metadata = response.json()
    chunks = metadata['chunks']
    owner = metadata.get('owner', 'anonymous')
    
    # Check authorization
    req_owner = request.headers.get('X-Owner')
    if owner != 'anonymous' and owner != req_owner:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Delete each chunk
    delete_results = []
    for chunk in chunks:
        chunk_id = chunk['chunk_id']
        node_url = chunk['node_url']
        
        # Delete chunk
        url = f"{node_url}/delete/{chunk_id}"
        headers = {'X-Owner': owner}
        try:
            response = requests.delete(url, headers=headers)
            delete_results.append({
                'chunk_id': chunk_id,
                'status': 'deleted' if response.status_code == 200 else 'failed'
            })
        except:
            delete_results.append({
                'chunk_id': chunk_id,
                'status': 'failed'
            })
    
    # TODO: Delete metadata from coordinator
    
    return jsonify({
        'status': 'success',
        'file_id': file_id,
        'chunks_deleted': delete_results
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)