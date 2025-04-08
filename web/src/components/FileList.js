import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Typography,
  IconButton,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Chip,
  Box,
  Alert
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import DownloadIcon from '@mui/icons-material/Download';
import LockIcon from '@mui/icons-material/Lock';
import LockOpenIcon from '@mui/icons-material/LockOpen';

function FileList({ files, onDelete, onDownload, userWallet }) {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState('');

  const handleDeleteClick = (file) => {
    setSelectedFile(file);
    setConfirmDelete(true);
  };

  const handleConfirmDelete = async () => {
    if (!selectedFile) return;
    
    try {
      await onDelete(selectedFile.file_id);
      setConfirmDelete(false);
      setSelectedFile(null);
    } catch (error) {
      setError(error.message || 'Failed to delete file');
    }
  };

  const handleCancelDelete = () => {
    setConfirmDelete(false);
    setSelectedFile(null);
  };

  const formatSize = (bytes) => {
    if (!bytes) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (timestamp) => {
    if (!timestamp) return 'Unknown';
    return new Date(timestamp * 1000).toLocaleString();
  };

  const isOwner = (file) => {
    if (!userWallet || !file.owner) return false;
    return userWallet.address.toLowerCase() === file.owner.toLowerCase();
  };

  return (
    <>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      
      <Typography variant="h5" component="h2" gutterBottom>
        Your Files
      </Typography>

      {files.length === 0 ? (
        <Typography variant="body1" color="textSecondary" sx={{ my: 4, textAlign: 'center' }}>
          No files found. Upload your first file to get started!
        </Typography>
      ) : (
        <TableContainer component={Paper}>
          <Table sx={{ minWidth: 650 }}>
            <TableHead>
              <TableRow>
                <TableCell>Filename</TableCell>
                <TableCell align="right">Size</TableCell>
                <TableCell align="right">Date</TableCell>
                <TableCell align="right">Security</TableCell>
                <TableCell align="right">Owner</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {files.map((file) => (
                <TableRow key={file.file_id}>
                  <TableCell component="th" scope="row">
                    {file.filename}
                  </TableCell>
                  <TableCell align="right">{formatSize(file.size)}</TableCell>
                  <TableCell align="right">{formatDate(file.created_at)}</TableCell>
                  <TableCell align="right">
                    {file.encryption === 'aes' ? (
                      <Chip 
                        icon={<LockIcon />} 
                        label="Encrypted" 
                        color="success" 
                        variant="outlined" 
                      />
                    ) : (
                      <Chip 
                        icon={<LockOpenIcon />} 
                        label="Not Encrypted" 
                        color="warning" 
                        variant="outlined" 
                      />
                    )}
                  </TableCell>
                  <TableCell align="right">
                    {file.owner === 'anonymous' ? (
                      'Anonymous'
                    ) : (
                      <Chip 
                        label={file.owner.substring(0, 6) + '...' + file.owner.substring(file.owner.length - 4)} 
                        size="small" 
                        color={isOwner(file) ? "primary" : "default"}
                      />
                    )}
                  </TableCell>
                  <TableCell align="right">
                    <Box>
                      <IconButton 
                        color="primary" 
                        onClick={() => onDownload(file.file_id)} 
                        title="Download"
                      >
                        <DownloadIcon />
                      </IconButton>
                      
                      {(file.owner === 'anonymous' || isOwner(file)) && (
                        <IconButton 
                          color="error" 
                          onClick={() => handleDeleteClick(file)} 
                          title="Delete"
                        >
                          <DeleteIcon />
                        </IconButton>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={confirmDelete}
        onClose={handleCancelDelete}
      >
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the file "{selectedFile?.filename}"? 
            This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCancelDelete} color="primary">
            Cancel
          </Button>
          <Button onClick={handleConfirmDelete} color="error" autoFocus>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

export default FileList; 