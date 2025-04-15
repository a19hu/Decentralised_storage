import json
import os
import sys
from web3 import Web3
import solcx

try:
    solcx.install_solc('0.8.0')
except Exception as e:
    print(f"Error installing solc: {e}")

BLOCKCHAIN_URL = os.getenv('BLOCKCHAIN_URL', 'http://localhost:8545')
w3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_URL))

if not w3.is_connected():
    sys.exit(1)

def compile_contract():
    contract_path = './StorageContract.sol'
    
    try:
        compiled_sol = solcx.compile_files(
            [contract_path],
            output_values=['abi', 'bin'],
            solc_version='0.8.0'
        )
        
        contract_id = f"{contract_path}:StorageContract"
        contract_interface = compiled_sol[contract_id]
        
        abi = contract_interface['abi']
        bytecode = contract_interface['bin']
        
        return abi, bytecode
    except Exception as e:
        print(f"Error compiling contract: {e}")
        sys.exit(1)

def deploy_contract(abi, bytecode):
    w3.eth.default_account = w3.eth.accounts[0]
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    try:
        tx_hash = Contract.constructor().transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        contract_address = tx_receipt.contractAddress
        print(f"Contract deployed! Address: {contract_address}")
        return contract_address
    except Exception as e:
        print(f"Error deploying contract: {e}")
        sys.exit(1)

def save_contract_info(abi, contract_address):
    data_dir = '../coordinator/data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory: {data_dir}")
    
    
    address_file = os.path.join(data_dir, 'contract_address.txt')
    with open(address_file, 'w') as f:
        f.write(contract_address)
    
    abi_file = os.path.join(data_dir, 'contract_abi.json')
    with open(abi_file, 'w') as f:
        json.dump(abi, f)
    

if __name__ == "__main__":
    abi, bytecode = compile_contract()
    contract_address = deploy_contract(abi, bytecode)
    save_contract_info(abi, contract_address)
    print("Contract deployment completed successfully!") 