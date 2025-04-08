import React, { useState } from 'react';
import { 
  Button, 
  Box, 
  TextField, 
  Typography, 
  Paper, 
  Grid,
  FormControl,
  FormControlLabel,
  RadioGroup,
  Radio,
  Alert,
  LinearProgress
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

function FileUpload({ onUpload, wallet }) {
  const [file, setFile] = useState(null);
  const [owner, setOwner] = useState('');
  const [encryption, setEncryption] = useState('aes');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a file to upload');
      return;
    }
    
    try {
      setLoading(true);
      setError('');
      setSuccess('');
      
      const result = await onUpload(file, wallet ? wallet.address : owner);
      
      setSuccess(`File uploaded successfully! File ID: ${result.file_id}`);
      setFile(null);
      e.target.reset();
    } catch (error) {
      setError(error.message || 'Failed to upload file');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" component="h2" gutterBottom>
        Upload File
      </Typography>
      
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
      
      <form onSubmit={handleSubmit}>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <Box 
              sx={{ 
                border: '2px dashed #ccc', 
                p: 3, 
                textAlign: 'center',
                borderRadius: 1,
                mb: 2,
                cursor: 'pointer',
                '&:hover': {
                  backgroundColor: '#f9f9f9'
                }
              }}
              onClick={() => document.getElementById('file-input').click()}
            >
              <input
                id="file-input"
                type="file"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <CloudUploadIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="body1">
                {file ? `Selected: ${file.name}` : 'Click to select a file'}
              </Typography>
              {file && (
                <Typography variant="body2" color="textSecondary">
                  Size: {(file.size / 1024).toFixed(2)} KB
                </Typography>
              )}
            </Box>
          </Grid>
          
          {!wallet && (
            <Grid item xs={12}>
              <TextField
                label="Owner Address (optional)"
                variant="outlined"
                fullWidth
                placeholder="0x..."
                helperText="Leave empty for anonymous upload"
                value={owner}
                onChange={(e) => setOwner(e.target.value)}
              />
            </Grid>
          )}
          
          <Grid item xs={12}>
            <FormControl component="fieldset">
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Encryption Method
              </Typography>
              <RadioGroup 
                row 
                value={encryption} 
                onChange={(e) => setEncryption(e.target.value)}
              >
                <FormControlLabel 
                  value="aes" 
                  control={<Radio />} 
                  label="AES Encryption" 
                />
                <FormControlLabel 
                  value="none" 
                  control={<Radio />} 
                  label="No Encryption" 
                />
              </RadioGroup>
            </FormControl>
          </Grid>
          
          <Grid item xs={12}>
            {loading ? (
              <Box sx={{ width: '100%' }}>
                <LinearProgress />
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Uploading and encrypting file...
                </Typography>
              </Box>
            ) : (
              <Button 
                variant="contained" 
                color="primary" 
                type="submit"
                startIcon={<CloudUploadIcon />}
              >
                Upload to Decentralized Storage
              </Button>
            )}
          </Grid>
        </Grid>
      </form>
    </Paper>
  );
}

export default FileUpload; 