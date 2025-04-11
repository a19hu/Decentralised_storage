import React, { useState } from 'react';
import { 
  Typography, 
  Box, 
  Button, 
  LinearProgress, 
  Paper, 
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

const FileUpload = ({ onUpload, wallet, agreements }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [selectedAgreement, setSelectedAgreement] = useState('');

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setUploadSuccess(false);
      setUploadError(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadError('Please select a file first');
      return;
    }

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(false);

    try {
      await onUpload(selectedFile, null, selectedAgreement || null);
      setUploadSuccess(true);
      setSelectedFile(null);
      // Reset the file input
      const fileInput = document.getElementById('file-upload');
      if (fileInput) {
        fileInput.value = '';
      }
    } catch (error) {
      setUploadError(error.message || 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Upload Files
      </Typography>
      
      <Paper
        sx={{
          p: 3,
          mb: 2,
          border: '2px dashed #ccc',
          textAlign: 'center',
          cursor: 'pointer',
          bgcolor: 'background.default',
          '&:hover': {
            bgcolor: 'action.hover',
          },
        }}
        onClick={() => document.getElementById('file-upload').click()}
      >
        <input
          type="file"
          id="file-upload"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
        <CloudUploadIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          Click to select file or drag and drop
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {selectedFile ? `Selected: ${selectedFile.name}` : 'No file selected'}
        </Typography>
      </Paper>

      {wallet && agreements && agreements.length > 0 && (
        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel id="agreement-select-label">Upload to rented storage</InputLabel>
          <Select
            labelId="agreement-select-label"
            id="agreement-select"
            value={selectedAgreement}
            label="Upload to rented storage"
            onChange={(e) => setSelectedAgreement(e.target.value)}
          >
            <MenuItem value="">
              <em>Standard storage (not rented)</em>
            </MenuItem>
            {agreements.map((agreement) => (
              <MenuItem 
                key={agreement.agreement_id} 
                value={agreement.agreement_id}
              >
                {agreement.node_id} - {agreement.size_mb}MB
              </MenuItem>
            ))}
          </Select>
          <FormHelperText>
            {selectedAgreement 
              ? "Your file will be encrypted and stored in the rented storage" 
              : "Upload to standard storage nodes"}
          </FormHelperText>
        </FormControl>
      )}

      {uploading && (
        <Box sx={{ width: '100%', mb: 2 }}>
          <LinearProgress />
        </Box>
      )}
      
      {uploadSuccess && (
        <Alert severity="success" sx={{ mb: 2 }}>
          File uploaded successfully!
        </Alert>
      )}
      
      {uploadError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {uploadError}
        </Alert>
      )}
      
      <Button
        variant="contained"
        onClick={handleUpload}
        disabled={!selectedFile || uploading}
        fullWidth
      >
        {uploading ? 'Uploading...' : 'Upload'}
      </Button>
    </Box>
  );
};

export default FileUpload; 