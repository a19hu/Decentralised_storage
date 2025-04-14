import React, { useState, useEffect } from 'react';
import { 
  Button, 
  Box, 
  Menu, 
  MenuItem, 
  ListItemIcon, 
  ListItemText,
  CircularProgress,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Alert
} from '@mui/material';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import LogoutIcon from '@mui/icons-material/Logout';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';

function WalletConnection({ wallet, setWallet }) {
  const [anchorEl, setAnchorEl] = useState(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [errorDialog, setErrorDialog] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [isCopied, setIsCopied] = useState(false);

  useEffect(() => {
    // Check if wallet was previously connected
    const savedWallet = localStorage.getItem('wallet');
    if (savedWallet) {
      try {
        setWallet(JSON.parse(savedWallet));
      } catch (error) {
        console.error('Failed to parse saved wallet', error);
        localStorage.removeItem('wallet');
      }
    }

    // Add ethereum provider event listeners
    if (window.ethereum) {
      window.ethereum.on('accountsChanged', handleAccountsChanged);
      window.ethereum.on('chainChanged', () => window.location.reload());
    }

    return () => {
      // Clean up listeners
      if (window.ethereum) {
        window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
      }
    };
  }, []);

  const handleAccountsChanged = (accounts) => {
    if (accounts.length === 0) {
      // User disconnected their wallet
      disconnectWallet();
    } else if (wallet && accounts[0] !== wallet.address) {
      // Account changed, update the wallet info
      const newWallet = {
        ...wallet,
        address: accounts[0]
      };
      setWallet(newWallet);
      localStorage.setItem('wallet', JSON.stringify(newWallet));
    }
  };

  const connectWallet = async () => {
    if (!window.ethereum) {
      setErrorMessage('No Ethereum wallet detected. Please install MetaMask or another web3 wallet.');
      setErrorDialog(true);
      return;
    }

    setIsConnecting(true);
    try {
      const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
      const currentAccount = accounts[0];
      
      const chainId = await window.ethereum.request({ method: 'eth_chainId' });
      const networkName = getNetworkName(chainId);
      
      const newWallet = {
        address: currentAccount,
        networkId: chainId,
        networkName: networkName
      };
      
      setWallet(newWallet);
      localStorage.setItem('wallet', JSON.stringify(newWallet));
    } catch (error) {
      console.error('Error connecting wallet:', error);
      setErrorMessage(error.message || 'Failed to connect wallet');
      setErrorDialog(true);
    } finally {
      setIsConnecting(false);
    }
  };

  const disconnectWallet = () => {
    setWallet(null);
    localStorage.removeItem('wallet');
    setAnchorEl(null);
  };

  const copyAddress = () => {
    if (wallet) {
      navigator.clipboard.writeText(wallet.address);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    }
    setAnchorEl(null);
  };

  const getNetworkName = (chainId) => {
    const networks = {
      '0x1': 'Ethereum Mainnet',
      '0x3': 'Ropsten Testnet',
      '0x4': 'Rinkeby Testnet',
      '0x5': 'Goerli Testnet',
      '0x2a': 'Kovan Testnet',
      '0x539': 'Ganache Local'
    };
    return networks[chainId] || `Chain ID: ${chainId}`;
  };

  const shortenAddress = (address) => {
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
  };

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  return (
    <>
      {wallet ? (
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Chip
            icon={<AccountBalanceIcon />}
            label={wallet.networkName}
            size="small"
            color="primary"
            variant="outlined"
            sx={{ mr: 1 }}
          />
          <Button
            variant="outlined"
            color="primary"
            onClick={handleClick}
            startIcon={<AccountBalanceWalletIcon />}
          >
            {shortenAddress(wallet.address)}
          </Button>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleClose}
          >
            <MenuItem onClick={copyAddress}>
              <ListItemIcon>
                <ContentCopyIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>
                {isCopied ? 'Address Copied!' : 'Copy Address'}
              </ListItemText>
            </MenuItem>
            <MenuItem onClick={disconnectWallet}>
              <ListItemIcon>
                <LogoutIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Disconnect</ListItemText>
            </MenuItem>
          </Menu>
        </Box>
      ) : (
        <Button
          variant="contained"
          color="primary"
          onClick={connectWallet}
          startIcon={isConnecting ? <CircularProgress size={20} color="inherit" /> : <AccountBalanceWalletIcon />}
          disabled={isConnecting}
        >
          {isConnecting ? 'Connecting...' : 'Connect Wallet'}
        </Button>
      )}

      {/* Error Dialog */}
      <Dialog
        open={errorDialog}
        onClose={() => setErrorDialog(false)}
      >
        <DialogTitle>Wallet Connection Error</DialogTitle>
        <DialogContent>
          <DialogContentText>
            <Alert severity="error" sx={{ mb: 2 }}>
              {errorMessage}
            </Alert>
            Please make sure you have a Web3 wallet extension installed like MetaMask.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setErrorDialog(false)} color="primary" autoFocus>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

export default WalletConnection; 