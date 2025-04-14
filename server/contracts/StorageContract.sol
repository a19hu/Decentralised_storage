// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract StorageContract {
    struct StorageProvider {
        address payable wallet;
        string nodeId;
        uint256 pricePerMB;
        bool active;
    }
    
    struct StorageAgreement {
        address user;
        string nodeId;
        uint256 sizeInMB;
        uint256 duration; // Duration in days
        uint256 totalPrice;
        uint256 startTime;
        bool active;
        string encryptionKeyHash; // Hash of encryption key
    }
    
    struct LockedStorage {
        string nodeId;
        uint256 sizeInMB;
        bool locked;  // Storage is locked for seller's access
    }
    
    mapping(string => StorageProvider) public storageProviders;
    mapping(address => StorageAgreement[]) public userAgreements;
    mapping(string => StorageAgreement[]) public providerAgreements;
    mapping(string => LockedStorage) public lockedStorageByNodeId;
    mapping(string => string) private encryptionKeys; // Maps agreement ID to encrypted key
    
    uint256 public platformFeePercent = 5; // 5% platform fee
    address payable public owner;
    
    event ProviderRegistered(string nodeId, address provider, uint256 pricePerMB);
    event AgreementCreated(address indexed user, string nodeId, uint256 sizeInMB, uint256 duration);
    event PaymentReleased(address indexed user, string nodeId, uint256 amount);
    event StorageLocked(string nodeId, uint256 sizeInMB);
    event EncryptionKeyStored(string agreementId, address indexed client);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    constructor() {
        owner = payable(msg.sender);
    }
    
    function registerProvider(string memory nodeId, uint256 pricePerMB) public {
        require(bytes(nodeId).length > 0, "NodeID cannot be empty");
        require(pricePerMB > 0, "Price must be greater than 0");
        
        storageProviders[nodeId] = StorageProvider({
            wallet: payable(msg.sender),
            nodeId: nodeId,
            pricePerMB: pricePerMB,
            active: true
        });
        
        emit ProviderRegistered(nodeId, msg.sender, pricePerMB);
    }
    
    function lockStorage(string memory nodeId, uint256 sizeInMB) public {
        StorageProvider storage provider = storageProviders[nodeId];
        require(provider.wallet == msg.sender, "Only provider can lock their storage");
        
        lockedStorageByNodeId[nodeId] = LockedStorage({
            nodeId: nodeId,
            sizeInMB: sizeInMB,
            locked: true
        });
        
        emit StorageLocked(nodeId, sizeInMB);
    }
    
    function createStorageAgreement(string memory nodeId, uint256 sizeInMB, uint256 durationInDays, string memory encryptionKeyHash) public payable {
        StorageProvider storage provider = storageProviders[nodeId];
        require(provider.active, "Provider is not active");
        
        // Check if storage is locked and available
        LockedStorage storage lockedStorage = lockedStorageByNodeId[nodeId];
        require(lockedStorage.locked, "Storage is not locked and ready for rental");
        require(lockedStorage.sizeInMB >= sizeInMB, "Insufficient storage available");
        
        uint256 totalPrice = sizeInMB * provider.pricePerMB * durationInDays;
        require(msg.value >= totalPrice, "Insufficient payment");
        
        // Generate agreement ID
        string memory agreementId = string(abi.encodePacked(nodeId, "-", toString(sizeInMB)));
        
        StorageAgreement memory agreement = StorageAgreement({
            user: msg.sender,
            nodeId: nodeId,
            sizeInMB: sizeInMB,
            duration: durationInDays,
            totalPrice: totalPrice,
            startTime: block.timestamp,
            active: true,
            encryptionKeyHash: encryptionKeyHash
        });
        
        userAgreements[msg.sender].push(agreement);
        providerAgreements[nodeId].push(agreement);
        
        // Update locked storage amount
        lockedStorage.sizeInMB -= sizeInMB;
        
        emit AgreementCreated(msg.sender, nodeId, sizeInMB, durationInDays);
        
        // Transfer payment to provider (minus platform fee)
        uint256 platformFee = (totalPrice * platformFeePercent) / 100;
        uint256 providerAmount = totalPrice - platformFee;
        
        provider.wallet.transfer(providerAmount);
        owner.transfer(platformFee);
        
        // Return excess payment if any
        if (msg.value > totalPrice) {
            payable(msg.sender).transfer(msg.value - totalPrice);
        }
    }
    
    function storeEncryptionKey(string memory agreementId, string memory encryptedKey) public {
        // Verify that sender is a client with agreement
        bool isValid = false;
        StorageAgreement[] storage agreements = userAgreements[msg.sender];
        
        for (uint i = 0; i < agreements.length; i++) {
            string memory currentAgreementId = string(abi.encodePacked(agreements[i].nodeId, "-", toString(agreements[i].sizeInMB)));
            if (keccak256(bytes(currentAgreementId)) == keccak256(bytes(agreementId))) {
                isValid = true;
                break;
            }
        }
        
        require(isValid, "Sender is not authorized for this agreement");
        
        // Store the encrypted key
        encryptionKeys[agreementId] = encryptedKey;
        
        emit EncryptionKeyStored(agreementId, msg.sender);
    }
    
    function getEncryptionKey(string memory agreementId) public view returns (string memory) {
        // Only the client can retrieve the key
        bool isValid = false;
        StorageAgreement[] storage agreements = userAgreements[msg.sender];
        
        for (uint i = 0; i < agreements.length; i++) {
            string memory currentAgreementId = string(abi.encodePacked(agreements[i].nodeId, "-", toString(agreements[i].sizeInMB)));
            if (keccak256(bytes(currentAgreementId)) == keccak256(bytes(agreementId))) {
                isValid = true;
                break;
            }
        }
        
        require(isValid, "Sender is not authorized to access this key");
        
        return encryptionKeys[agreementId];
    }
    
    function getUserAgreements() public view returns (StorageAgreement[] memory) {
        return userAgreements[msg.sender];
    }
    
    function getProviderAgreements(string memory nodeId) public view returns (StorageAgreement[] memory) {
        StorageProvider storage provider = storageProviders[nodeId];
        require(msg.sender == provider.wallet, "Only provider can view their agreements");
        return providerAgreements[nodeId];
    }
    
    function setPlatformFee(uint256 newFeePercent) public onlyOwner {
        require(newFeePercent <= 20, "Fee cannot exceed 20%");
        platformFeePercent = newFeePercent;
    }
    
    function withdrawPlatformFees() public onlyOwner {
        owner.transfer(address(this).balance);
    }
    
    // Helper function to convert uint to string
    function toString(uint256 value) internal pure returns (string memory) {
        if (value == 0) {
            return "0";
        }
        
        uint256 temp = value;
        uint256 digits;
        
        while (temp != 0) {
            digits++;
            temp /= 10;
        }
        
        bytes memory buffer = new bytes(digits);
        
        while (value != 0) {
            digits -= 1;
            buffer[digits] = bytes1(uint8(48 + uint256(value % 10)));
            value /= 10;
        }
        
        return string(buffer);
    }
} 