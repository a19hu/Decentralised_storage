import React, { useState, useEffect } from 'react';
import { Container, Typography, Box, AppBar, Toolbar, Button, Paper } from '@mui/material';
import FileUpload from './components/FileUpload';
import FileList from './components/FileList';
import NodeStatus from './components/NodeStatus';
import WalletConnection from './components/WalletConnection';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Import new components
import StorageMarket from './components/StorageMarket';
import SellerDashboard from './components/SellerDashboard';

// API URL
// const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5002';
const API_URLs = 'http://172.31.112.248:5001';
const API_URL = 'http://172.31.112.248:5002';


// Create a theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#2196f3',
    },
    secondary: {
      main: '#4caf50',
    },
    background: {
      default: '#f5f5f5',
    },
  },
});

function App() {
  const [files, setFiles] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [wallet, setWallet] = useState(null);
  const [activeTab, setActiveTab] = useState('files');
  const [agreements, setAgreements] = useState([]);
  const [providers, setProviders] = useState([]);

  // Fetch files when component mounts or wallet changes
  useEffect(() => {
    fetchFiles();
    fetchNodes();
    if (wallet) {
      fetchUserAgreements();
      fetchAvailableProviders();
    }
  }, [wallet]);

  const fetchFiles = async () => {
    try {
      let url = `${API_URL}/list_files`;
      if (wallet) {
        url += `?owner=${wallet.address}`;
      }
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setFiles(data);
      }
    } catch (error) {
      console.error('Error fetching files:', error);
    }
  };

  const fetchNodes = async () => {
    try {
      const response = await fetch(`${API_URLs}/all_nodes`);
      if (response.ok) {
        const data = await response.json();
        setNodes(data);
      }
    } catch (error) {
      console.error('Error fetching nodes:', error);
    }
  };

  const fetchUserAgreements = async () => {
    try {
      if (!wallet) return;
      
      const response = await fetch(`${API_URL}/user_agreements?wallet_address=${wallet.address}`);
      if (response.ok) {
        const data = await response.json();
        setAgreements(data);
      }
    } catch (error) {
      console.error('Error fetching agreements:', error);
    }
  };

  const fetchAvailableProviders = async () => {
    try {
      const response = await fetch(`${API_URL}/available_storage_providers`);
      if (response.ok) {
        const data = await response.json();
        setProviders(data);
      }
    } catch (error) {
      console.error('Error fetching storage providers:', error);
    }
  };

  const handleFileUpload = async (file, owner, agreementId) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      if (wallet) {
        formData.append('owner', wallet.address);
      } else if (owner) {
        formData.append('owner', owner);
      }

      if (agreementId) {
        formData.append('agreement_id', agreementId);
      }
      console.log('Uploading file:', file);
      const response = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        fetchFiles();
        return await response.json();
      } else {
        const error = await response.json();
        throw new Error(error.error || 'Upload failed');
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      throw error;
    }
  };

  const handleFileDelete = async (fileId) => {
    try {
      const headers = {};
      if (wallet) {
        headers['X-Owner'] = wallet.address;
      }

      const response = await fetch(`${API_URL}/delete/${fileId}`, {
        method: 'DELETE',
        headers: headers,
      });

      if (response.ok) {
        fetchFiles();
        return await response.json();
      } else {
        const error = await response.json();
        throw new Error(error.error || 'Delete failed');
      }
    } catch (error) {
      console.error('Error deleting file:', error);
      throw error;
    }
  };

  const handleFileDownload = (fileId) => {
    const headers = {};
    if (wallet) {
      headers['X-Owner'] = wallet.address;
    }
    window.open(`${API_URL}/download/${fileId}`, '_blank');
  };

  const handleLockStorage = async (sizeMB) => {
    try {
      if (!wallet) {
        throw new Error('Wallet connection required');
      }

      // Find the node that belongs to this wallet
      const userNode = nodes.find(node => 
        node.wallet_address && node.wallet_address.toLowerCase() === wallet.address.toLowerCase()
      );

      if (!userNode) {
        throw new Error('No storage node found for this wallet');
      }

      const response = await fetch(`${userNode.url}/lock_storage`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          size_mb: sizeMB
        })
      });

      if (response.ok) {
        fetchNodes();
        return await response.json();
      } else {
        const error = await response.json();
        throw new Error(error.error || 'Failed to lock storage');
      }
    } catch (error) {
      console.error('Error locking storage:', error);
      throw error;
    }
  };

  const handleRentStorage = async (nodeId, sizeMB, durationDays) => {
    console.log('Renting storage:', nodeId, sizeMB, durationDays);
    try {
      if (!wallet) {
        throw new Error('Wallet connection required');
      }

      const response = await fetch(`${API_URL}/rent_storage`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          node_id: nodeId,
          size_mb: sizeMB,
          duration_days: durationDays,
          wallet_address: wallet.address
        })
      });

      if (response.ok) {
        const result = await response.json();
        fetchUserAgreements();
        return result;
      } else {
        const error = await response.json();
        throw new Error(error.error || 'Failed to rent storage');
      }
    } catch (error) {
      console.error('Error renting storage:', error);
      throw error;
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Decentralized Storage
          </Typography>
          <WalletConnection wallet={wallet} setWallet={setWallet} />
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box sx={{ mb: 4 }}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', mb: 2, flexWrap: 'wrap' }}>
              <Button 
                variant={activeTab === 'files' ? 'contained' : 'outlined'} 
                onClick={() => setActiveTab('files')}
                sx={{ mr: 1, mb: 1 }}
              >
                My Files
              </Button>
              <Button 
                variant={activeTab === 'upload' ? 'contained' : 'outlined'}
                onClick={() => setActiveTab('upload')}
                sx={{ mr: 1, mb: 1 }}
              >
                Upload
              </Button>
              <Button 
                variant={activeTab === 'nodes' ? 'contained' : 'outlined'}
                onClick={() => setActiveTab('nodes')}
                sx={{ mr: 1, mb: 1 }}
              >
                Storage Nodes
              </Button>
              <Button 
                variant={activeTab === 'market' ? 'contained' : 'outlined'}
                onClick={() => setActiveTab('market')}
                sx={{ mr: 1, mb: 1 }}
              >
                Storage Market
              </Button>
              <Button 
                variant={activeTab === 'seller' ? 'contained' : 'outlined'}
                onClick={() => setActiveTab('seller')}
                sx={{ mr: 1, mb: 1 }}
              >
                Seller Dashboard
              </Button>
            </Box>

            {activeTab === 'files' && (
              <FileList 
                files={files} 
                onDelete={handleFileDelete} 
                onDownload={handleFileDownload}
                userWallet={wallet}
                agreements={agreements}
              />
            )}
            
            {activeTab === 'upload' && (
              <FileUpload 
                onUpload={handleFileUpload} 
                wallet={wallet} 
                agreements={agreements}
              />
            )}
            
            {activeTab === 'nodes' && (
              <NodeStatus nodes={nodes} />
            )}

            {activeTab === 'market' && (
              <StorageMarket 
                providers={providers}
                onRent={handleRentStorage}
                wallet={wallet}
                agreements={agreements}
              />
            )}

            {activeTab === 'seller' && (
              <SellerDashboard 
                nodes={nodes}
                onLockStorage={handleLockStorage}
                wallet={wallet}
              />
            )}
          </Paper>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App; 