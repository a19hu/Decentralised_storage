import React, { useState } from 'react';
import { 
  Typography, 
  Box, 
  Button, 
  Card, 
  CardContent, 
  TextField,
  Alert,
  Grid,
  Paper,
  LinearProgress,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions
} from '@mui/material';

const SellerDashboard = ({ nodes, onLockStorage, wallet }) => {
  const [sizeMB, setSizeMB] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);

  // Find the node owned by the current wallet
  const findUserNode = () => {
    if (!wallet || !nodes) return null;
    
    return nodes.find(node => 
      node.wallet_address && node.wallet_address.toLowerCase() === wallet.address.toLowerCase()
    );
  };

  const userNode = findUserNode();

  const handleLockStorage = async () => {
    if (!wallet) {
      setError('Please connect your wallet first');
      return;
    }

    if (!userNode) {
      setError('No storage node found for your wallet');
      return;
    }

    if (sizeMB <= 0) {
      setError('Size must be greater than 0');
      return;
    }

    const availableSpace = userNode.limit_mb - userNode.used_mb - (userNode.locked_mb || 0);
    if (sizeMB > availableSpace) {
      setError(`You only have ${availableSpace}MB available to lock`);
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const result = await onLockStorage(sizeMB);
      setSuccess(`Successfully locked ${sizeMB}MB of storage for rental!`);
      setSizeMB(1);
      setTimeout(() => {
        setSuccess('');
        setDialogOpen(false);
      }, 3000);
    } catch (err) {
      setError(err.message || 'Failed to lock storage');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = () => {
    setDialogOpen(true);
    setError('');
    setSuccess('');
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
  };

  const calculateStoragePercentage = (node) => {
    if (!node) return 0;
    const total = node.limit_mb;
    if (!total) return 0;
    
    const used = node.used_mb || 0;
    const locked = node.locked_mb || 0;
    return Math.round(((used + locked) / total) * 100);
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Seller Dashboard
      </Typography>

      {!wallet && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Connect your wallet to manage your storage offerings
        </Alert>
      )}

      {wallet && !userNode && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          No storage node found for your wallet. Make sure your node is registered.
        </Alert>
      )}

      {userNode && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Your Storage Node: {userNode.node_id}
          </Typography>
          
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body1">
                  Storage Capacity: {userNode.limit_mb}MB
                </Typography>
                <Typography variant="body1">
                  Used: {userNode.used_mb}MB
                </Typography>
                <Typography variant="body1">
                  Locked for Rental: {userNode.locked_mb || 0}MB
                </Typography>
                <Typography variant="body1">
                  Available: {userNode.limit_mb - userNode.used_mb - (userNode.locked_mb || 0)}MB
                </Typography>
              </Box>
              
              <Typography variant="body2" gutterBottom>
                Storage Usage
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Box sx={{ width: '100%', mr: 1 }}>
                  <LinearProgress 
                    variant="determinate" 
                    value={calculateStoragePercentage(userNode)} 
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                </Box>
                <Box sx={{ minWidth: 35 }}>
                  <Typography variant="body2" color="text.secondary">
                    {calculateStoragePercentage(userNode)}%
                  </Typography>
                </Box>
              </Box>
              
              <Button 
                variant="contained" 
                color="primary" 
                onClick={handleOpenDialog}
                disabled={!wallet || userNode.limit_mb - userNode.used_mb - (userNode.locked_mb || 0) <= 0}
                sx={{ mt: 2 }}
              >
                Lock Storage for Rental
              </Button>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Your Earnings
                  </Typography>
                  <Typography variant="body1">
                    Current Rate: {userNode.price_per_mb || 1} wei/MB/day
                  </Typography>
                  <Typography variant="body1">
                    Storage Rented: {userNode.locked_mb ? (userNode.locked_mb - (userNode.available_mb || 0)) : 0}MB
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Chip 
                      label={`${userNode.wallet_address ? userNode.wallet_address.substring(0, 6) + '...' + userNode.wallet_address.substring(userNode.wallet_address.length - 4) : 'No wallet'}`}
                      color="primary"
                      variant="outlined"
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Paper>
      )}

      <Dialog open={dialogOpen} onClose={handleCloseDialog}>
        <DialogTitle>Lock Storage for Rental</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Choose how much storage to lock for rental. This space will be reserved for clients to purchase.
          </DialogContentText>
          
          {error && <Alert severity="error" sx={{ mt: 2, mb: 2 }}>{error}</Alert>}
          {success && <Alert severity="success" sx={{ mt: 2, mb: 2 }}>{success}</Alert>}
          
          <TextField
            autoFocus
            margin="dense"
            label="Size (MB)"
            type="number"
            fullWidth
            variant="outlined"
            value={sizeMB}
            onChange={(e) => setSizeMB(Math.max(1, parseInt(e.target.value) || 0))}
            InputProps={{ 
              inputProps: { 
                min: 1, 
                max: userNode ? userNode.limit_mb - userNode.used_mb - (userNode.locked_mb || 0) : 0 
              } 
            }}
            helperText={userNode ? `Maximum available: ${userNode.limit_mb - userNode.used_mb - (userNode.locked_mb || 0)}MB` : ''}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button 
            onClick={handleLockStorage} 
            variant="contained"
            disabled={loading || !wallet}
          >
            {loading ? 'Processing...' : 'Lock Storage'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SellerDashboard; 