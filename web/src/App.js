import React, { useState, useEffect } from 'react';
import { Container, Typography, Box, AppBar, Toolbar, Button, Paper } from '@mui/material';
import FileUpload from './components/FileUpload';
import FileList from './components/FileList';
import NodeStatus from './components/NodeStatus';
import WalletConnection from './components/WalletConnection';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// API URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5002';

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

  // Fetch files when component mounts or wallet changes
  useEffect(() => {
    fetchFiles();
    fetchNodes();
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
      const response = await fetch(`${API_URL}/all_nodes`);
      if (response.ok) {
        const data = await response.json();
        setNodes(data);
      }
    } catch (error) {
      console.error('Error fetching nodes:', error);
    }
  };

  const handleFileUpload = async (file, owner) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      if (wallet) {
        formData.append('owner', wallet.address);
      } else if (owner) {
        formData.append('owner', owner);
      }

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
    window.open(`${API_URL}/download/${fileId}`, '_blank');
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
            <Box sx={{ display: 'flex', mb: 2 }}>
              <Button 
                variant={activeTab === 'files' ? 'contained' : 'outlined'} 
                onClick={() => setActiveTab('files')}
                sx={{ mr: 1 }}
              >
                Files
              </Button>
              <Button 
                variant={activeTab === 'upload' ? 'contained' : 'outlined'}
                onClick={() => setActiveTab('upload')}
                sx={{ mr: 1 }}
              >
                Upload
              </Button>
              <Button 
                variant={activeTab === 'nodes' ? 'contained' : 'outlined'}
                onClick={() => setActiveTab('nodes')}
              >
                Storage Nodes
              </Button>
            </Box>

            {activeTab === 'files' && (
              <FileList 
                files={files} 
                onDelete={handleFileDelete} 
                onDownload={handleFileDownload}
                userWallet={wallet}
              />
            )}
            
            {activeTab === 'upload' && (
              <FileUpload onUpload={handleFileUpload} wallet={wallet} />
            )}
            
            {activeTab === 'nodes' && (
              <NodeStatus nodes={nodes} />
            )}
          </Paper>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App; 