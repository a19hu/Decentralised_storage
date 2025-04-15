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

COORDINATOR_URL = os.getenv('COORDINATOR_URL', 'http://localhost:5001')
BLOCKCHAIN_URL = os.getenv('BLOCKCHAIN_URL', 'http://localhost:8545')
TEMP_DIR = './temp'

if not os.path.exists(TEMP_DIR):
    try:
        os.makedirs(TEMP_DIR)
        print(f"Created temp directory: {TEMP_DIR}")
    except Exception as e:
        print(f"Error creating temp directory: {e}")
        raise

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_URL))

CONTRACT_ABI_PATH ='../coordinator/data/contract_abi.json'
CONTRACT_ADDRESS_FILE ='../coordinator/data/contract_address.txt'
contract = None
CONTRACT_ADDRESS = ''

# Read contract address from file if it exists
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
        print(contract)
        print(f"Contract loaded successfully at address {CONTRACT_ADDRESS}")
    except Exception as e:
        print(f"Error loading contract: {e}")

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

@app.route('/available_storage_providers', methods=['GET'])
def available_storage_providers():
    """Get list of available storage providers with available space for rental"""
    response = requests.get(f'{COORDINATOR_URL}/available_nodes')
    if response.status_code != 200:
        return jsonify({'error': 'Failed to get available storage nodes'}), 500
    
    nodes = response.json()
    
    # Filter for nodes with locked storage available
    providers = []
    for node in nodes:
        if 'locked_mb' in node and node['locked_mb'] >= 0:
            providers.append({
                'node_id': node['node_id'],
                'available_mb': node['locked_mb'],
                'price_per_mb': node.get('price_per_mb', 1),
                'url': node['url']
            })
    
    return jsonify(providers), 200

@app.route('/rent_storage', methods=['POST'])
def rent_storage():
    """Rent storage from a provider and create a storage agreement"""
    print("Renting storage...")
    data = request.json
    node_id = data.get('node_id')
    size_mb = data.get('size_mb')
    duration_days = data.get('duration_days', 30)
    wallet_address = data.get('wallet_address')
    
    if not all([node_id, size_mb, wallet_address]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    # Generate encryption key for this storage agreement
    encryption_key = generate_encryption_key()
    encryption_key_b64 = base64.b64encode(encryption_key).decode('utf-8')
    key_hash = hashlib.sha256(encryption_key).hexdigest()
    
    # Create agreement on blockchain
    if not contract:
        return jsonify({'error': 'Smart contract not available'}), 500
    
    # Calculate price in wei based on provider's pricing
    response = requests.get(f'{COORDINATOR_URL}/available_nodes')
    provider = None
    for node in response.json():
        if node['node_id'] == node_id:
            provider = node
            break
    
    if not provider:
        return jsonify({'error': 'Provider not found'}), 404
    
    price_per_mb = provider.get('price_per_mb', 1)
    total_price = int(price_per_mb) * int(size_mb) * int(duration_days)
    
    try:
        # Convert wallet address to checksum format
        wallet_address = Web3.to_checksum_address(wallet_address)
        
        # Create storage agreement on blockchain
        tx_hash = contract.functions.createStorageAgreement(
            node_id,
            int(size_mb),
            int(duration_days),
            key_hash
        ).transact({
            'from': wallet_address,
            'value': total_price
        })
        
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        if tx_receipt.status != 1:
            return jsonify({'error': 'Blockchain transaction failed'}), 500
        
        # Generate agreement ID as node_id-size_mb
        agreement_id = f"{node_id}-{size_mb}"
        
        # Encrypt the encryption key with client's public key for secure storage on blockchain
        # For simplicity, we're just storing the encrypted key in the contract
        # In a real implementation, you would encrypt the key with the client's public key
        encrypted_key = encryption_key_b64
        
        # Store the encryption key on blockchain
        tx_hash = contract.functions.storeEncryptionKey(
            agreement_id,
            encrypted_key
        ).transact({'from': wallet_address})
        
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        if tx_receipt.status != 1:
            return jsonify({'error': 'Failed to store encryption key'}), 500
        
        return jsonify({
            'status': 'success',
            'agreement_id': agreement_id,
            'encryption_key': encryption_key_b64,  # In a real app, this would be securely transmitted
            'total_price': total_price
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error creating agreement: {str(e)}'}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file in request'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get optional parameters
        owner = request.form.get('owner', 'anonymous')
        encryption = request.form.get('encryption', 'aes')
        agreement_id = request.form.get('agreement_id')  # For rented storage
        print(f"Owner: {owner}, Encryption: {encryption}, Agreement ID: {agreement_id}")
        
        # Save file temporarily
        temp_path = os.path.join(TEMP_DIR, file.filename)
        file.save(temp_path)
        
        # Generate a file ID
        file_id = str(uuid.uuid4())
        
        # If using rented storage, get storage node information
        if agreement_id:
            # Extract node_id from agreement_id (format is node_id-size_mb)
            node_id = agreement_id.split('-')[0]
            
            # Get node information
            response = requests.get(f'{COORDINATOR_URL}/all_nodes')
            node_list = [node for node in response.json() if node['node_id'] == node_id]
            
            if not node_list:
                return jsonify({'error': f'Storage node {node_id} not found'}), 404
            
            # Get encryption key from blockchain
            if contract and owner != 'anonymous':
                try:
                    encrypted_key = contract.functions.getEncryptionKey(agreement_id).call({'from': owner})
                    key = base64.b64decode(encrypted_key)
                    encryption = 'aes'  # Force AES encryption for rented storage
                except Exception as e:
                    return jsonify({'error': f'Failed to get encryption key: {str(e)}'}), 500
        else:
            # For regular storage, get available nodes
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
            # Select a node using round-robin for regular storage, or specific node for rented storage
            node = node_list[i % len(node_list)] if not agreement_id else node_list[0]
            
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
            
            # If using rented storage, add agreement ID header
            if agreement_id:
                headers['X-Agreement-Id'] = agreement_id
            
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
                        'encryption': encryption_type,
                        'agreement_id': agreement_id
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
            'encryption': encryption,
            'agreement_id': agreement_id
        }
        
        # Store the encryption key if used
        if key and not agreement_id:  # For regular storage only
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
    
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

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
    agreement_id = metadata.get('agreement_id')
    
    # Sort chunks by index
    chunks.sort(key=lambda x: x['index'])
    
    # Create temp file to assemble the chunks
    temp_file = os.path.join(TEMP_DIR, filename)
    
    # Get encryption key
    key = None
    if encryption == 'aes':
        if agreement_id and contract:
            # Get key from blockchain for rented storage
            owner = request.headers.get('X-Owner')
            if not owner:
                return jsonify({'error': 'Owner address required for encrypted files'}), 400
            
            try:
                encrypted_key = contract.functions.getEncryptionKey(agreement_id).call({'from': owner})
                key = base64.b64decode(encrypted_key)
            except Exception as e:
                return jsonify({'error': f'Failed to get encryption key: {str(e)}'}), 500
        elif 'key' in metadata:
            # Get key from metadata for regular storage
            key = base64.b64decode(metadata['key'])
        else:
            return jsonify({'error': 'Encryption key not found'}), 500
    
    with open(temp_file, 'wb') as f:
        for chunk in chunks:
            chunk_id = chunk['chunk_id']
            node_url = chunk['node_url']
            
            # Download chunk
            headers = {}
            if agreement_id:
                headers = {
                    'X-Agreement-Id': agreement_id,
                    'X-Owner': request.headers.get('X-Owner', '')
                }
            
            url = f"{node_url}/retrieve/{chunk_id}"
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                return jsonify({'error': f'Failed to download chunk {chunk_id}'}), 500
            
            chunk_data = response.content
            
            # Decrypt if needed
            if encryption == 'aes' and key:
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
    agreement_id = request.args.get('agreement_id')
    
    # Call coordinator to list files
    url = f'{COORDINATOR_URL}/list_files'
    params = {}
    
    if owner:
        params['owner'] = owner
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return jsonify({'error': 'Failed to list files'}), 500
    
    files = response.json()
    
    # Filter by agreement_id if provided
    if agreement_id:
        files = [file for file in files if file.get('agreement_id') == agreement_id]
    
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
    
    # Check authorization
    owner = request.headers.get('X-Owner')
    if metadata['owner'] != 'anonymous' and metadata['owner'] != owner:
        return jsonify({'error': 'Not authorized to delete this file'}), 403
    
    # Get agreement ID if exists
    agreement_id = metadata.get('agreement_id')
    
    # Delete each chunk from storage nodes
    chunks = metadata['chunks']
    for chunk in chunks:
        chunk_id = chunk['chunk_id']
        node_url = chunk['node_url']
        
        # Delete chunk
        headers = {'X-Owner': owner}
        if agreement_id:
            headers['X-Agreement-Id'] = agreement_id
        
        url = f"{node_url}/delete/{chunk_id}"
        response = requests.delete(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to delete chunk {chunk_id}: {response.text}")
    
    # Delete file metadata from coordinator
    response = requests.delete(f'{COORDINATOR_URL}/delete_file_metadata/{file_id}', headers={'X-Owner': owner})
    if response.status_code != 200:
        return jsonify({'error': 'Failed to delete file metadata'}), 500
    
    return jsonify({'status': 'deleted', 'file_id': file_id}), 200

@app.route('/user_agreements', methods=['GET'])
def user_agreements():
    """Get list of storage agreements for a user"""
    wallet_address = request.args.get('wallet_address')
    
    if not wallet_address:
        return jsonify({'error': 'Wallet address is required'}), 400
    
    if not contract:
        return jsonify({'error': 'Smart contract not available'}), 500
    
    try:
        # Convert wallet address to checksum format
        wallet_address = Web3.to_checksum_address(wallet_address)
        
        # Call contract to get user agreements
        agreements = contract.functions.getUserAgreements().call({'from': wallet_address})
        
        return jsonify([{
            'node_id': agreement[1],
            'size_mb': agreement[2],
            'duration_days': agreement[3],
            'total_price': agreement[4],
            'start_time': agreement[5],
            'active': agreement[6],
            'agreement_id': f"{agreement[1]}-{agreement[2]}"
        } for agreement in agreements]), 200
        
    except Exception as e:
        return jsonify({'error': f'Error getting agreements: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)