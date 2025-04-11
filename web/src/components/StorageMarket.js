import React, { useState } from 'react';
import { 
  Typography, 
  Box, 
  Button, 
  Card, 
  CardContent, 
  CardActions, 
  Grid, 
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Alert,
  Chip
} from '@mui/material';

const StorageMarket = ({ providers, onRent, wallet, agreements }) => {
  const [selectedProvider, setSelectedProvider] = useState(null);
  const [sizeMB, setSizeMB] = useState(1);
  const [durationDays, setDurationDays] = useState(30);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleOpenDialog = (provider) => {
    setSelectedProvider(provider);
    setDialogOpen(true);
    setError('');
    setSuccess('');
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedProvider(null);
  };

  const handleRentStorage = async () => {
    if (!wallet) {
      setError('Please connect your wallet first');
      return;
    }

    if (sizeMB <= 0) {
      setError('Size must be greater than 0');
      return;
    }

    if (sizeMB > selectedProvider.available_mb) {
      setError(`Provider only has ${selectedProvider.available_mb}MB available`);
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const result = await onRent(selectedProvider.node_id, sizeMB, durationDays);
      setSuccess(`Successfully rented ${sizeMB}MB for ${durationDays} days! Agreement ID: ${result.agreement_id}`);
      setTimeout(() => {
        handleCloseDialog();
        setSuccess('');
      }, 3000);
    } catch (err) {
      setError(err.message || 'Failed to rent storage');
    } finally {
      setLoading(false);
    }
  };

  const calculatePrice = () => {
    if (!selectedProvider) return 0;
    return selectedProvider.price_per_mb * sizeMB * durationDays;
  };

  const isAlreadyRenting = (nodeId) => {
    return agreements && agreements.some(agreement => agreement.node_id === nodeId);
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Storage Market
      </Typography>

      {!wallet && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Connect your wallet to rent storage
        </Alert>
      )}

      {providers && providers.length === 0 ? (
        <Alert severity="info">
          No storage providers available at the moment
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {providers.map((provider) => (
            <Grid item xs={12} sm={6} md={4} key={provider.node_id}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Node: {provider.node_id}
                    {isAlreadyRenting(provider.node_id) && (
                      <Chip 
                        label="Active Agreement" 
                        color="success" 
                        size="small" 
                        sx={{ ml: 1 }}
                      />
                    )}
                  </Typography>
                  <Typography variant="body1">
                    Available: {provider.available_mb}MB
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Price: {provider.price_per_mb} wei/MB/day
                  </Typography>
                </CardContent>
                <CardActions>
                  <Button 
                    size="small" 
                    variant="contained" 
                    onClick={() => handleOpenDialog(provider)}
                    disabled={!wallet}
                  >
                    Rent Storage
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <Dialog open={dialogOpen} onClose={handleCloseDialog}>
        <DialogTitle>Rent Storage</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Rent storage from Node: {selectedProvider?.node_id}
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
            InputProps={{ inputProps: { min: 1, max: selectedProvider?.available_mb } }}
            helperText={`Maximum available: ${selectedProvider?.available_mb}MB`}
          />
          
          <TextField
            margin="dense"
            label="Duration (days)"
            type="number"
            fullWidth
            variant="outlined"
            value={durationDays}
            onChange={(e) => setDurationDays(Math.max(1, parseInt(e.target.value) || 0))}
            InputProps={{ inputProps: { min: 1 } }}
          />
          
          <Typography variant="body1" sx={{ mt: 2 }}>
            Total Cost: {calculatePrice()} wei
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button 
            onClick={handleRentStorage} 
            variant="contained"
            disabled={loading || !wallet}
          >
            {loading ? 'Processing...' : 'Rent Storage'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StorageMarket; 