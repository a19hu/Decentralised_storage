import React, { useState } from 'react';
import {
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
  Alert,
  List,
  ListItem,
  ListItemText,
  Divider
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import DownloadIcon from '@mui/icons-material/Download';
import LockIcon from '@mui/icons-material/Lock';
import FolderSpecialIcon from '@mui/icons-material/FolderSpecial';

const FileList = ({ files, onDelete, onDownload, userWallet, agreements }) => {
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleDeleteConfirm = (file) => {
    setSelectedFile(file);
    setDeleteConfirmOpen(true);
  };

  const handleDeleteCancel = () => {
    setDeleteConfirmOpen(false);
    setSelectedFile(null);
  };

  const handleDeleteFile = async () => {
    if (!selectedFile) return;
    
    setLoading(true);
    setError('');
    
    try {
      await onDelete(selectedFile.file_id);
      setDeleteConfirmOpen(false);
      setSelectedFile(null);
    } catch (err) {
      setError(err.message || 'Failed to delete file');
    } finally {
      setLoading(false);
    }
  };

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (timestamp) => {
    if (!timestamp) return 'Unknown';
    return new Date(timestamp * 1000).toLocaleString();
  };

  // Group files by storage type (rented or standard)
  const standardFiles = files.filter(file => !file.agreement_id);
  const rentedFiles = files.filter(file => file.agreement_id);

  // Check if a file is owned by the current user
  const isOwner = (file) => {
    if (!userWallet) return false;
    return file.owner === userWallet.address;
  };

  // Find agreement details for a file
  const getAgreementDetails = (agreementId) => {
    if (!agreements) return null;
    return agreements.find(agreement => agreement.agreement_id === agreementId);
  };

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Your Files
      </Typography>

      {files.length === 0 ? (
        <Alert severity="info">
          No files found. Upload some files to get started.
        </Alert>
      ) : (
        <>
          {rentedFiles.length > 0 && (
            <Box mb={3}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <FolderSpecialIcon sx={{ mr: 1 }} /> Files in Rented Storage
              </Typography>
              <Paper variant="outlined">
                <List>
                  {rentedFiles.map((file, index) => {
                    const agreementDetails = getAgreementDetails(file.agreement_id);
                    return (
                      <React.Fragment key={file.file_id}>
                        {index > 0 && <Divider />}
                        <ListItem
                          secondaryAction={
                            <Box>
                              <IconButton 
                                edge="end" 
                                onClick={() => onDownload(file.file_id)}
                                title="Download file"
                              >
                                <DownloadIcon />
                              </IconButton>
                              {isOwner(file) && (
                                <IconButton 
                                  edge="end" 
                                  onClick={() => handleDeleteConfirm(file)}
                                  title="Delete file"
                                >
                                  <DeleteIcon />
                                </IconButton>
                              )}
                            </Box>
                          }
                        >
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                {file.filename}
                                <Chip 
                                  icon={<LockIcon />} 
                                  label="Encrypted" 
                                  size="small" 
                                  color="primary" 
                                  variant="outlined"
                                  sx={{ ml: 1 }}
                                />
                              </Box>
                            }
                            secondary={
                              <>
                                <Typography component="span" variant="body2" color="text.primary">
                                  Size: {formatSize(file.size)}
                                </Typography>
                                <br />
                                <Typography component="span" variant="body2">
                                  Uploaded: {formatDate(file.created_at)}
                                </Typography>
                                <br />
                                <Typography component="span" variant="body2">
                                  Storage: {file.agreement_id} 
                                  {agreementDetails && ` (${agreementDetails.size_mb}MB)`}
                                </Typography>
                              </>
                            }
                          />
                        </ListItem>
                      </React.Fragment>
                    );
                  })}
                </List>
              </Paper>
            </Box>
          )}

          {standardFiles.length > 0 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Files in Standard Storage
              </Typography>
              <Paper variant="outlined">
                <List>
                  {standardFiles.map((file, index) => (
                    <React.Fragment key={file.file_id}>
                      {index > 0 && <Divider />}
                      <ListItem
                        secondaryAction={
                          <Box>
                          {isOwner(file) && (
                            <IconButton 
                              edge="end" 
                              onClick={() => onDownload(file.file_id)}
                              title="Download file"
                            >
                              <DownloadIcon />
                            </IconButton> )}
                            {isOwner(file) && (
                              <IconButton 
                                edge="end" 
                                onClick={() => handleDeleteConfirm(file)}
                                title="Delete file"
                              >
                                <DeleteIcon />
                              </IconButton>
                            )}
                          </Box>
                        }
                      >
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              {file.filename}
                              {file.encryption === 'aes' && (
                                <Chip 
                                  icon={<LockIcon />} 
                                  label="Encrypted" 
                                  size="small" 
                                  color="primary" 
                                  variant="outlined"
                                  sx={{ ml: 1 }}
                                />
                              )}
                            </Box>
                          }
                          secondary={
                            <>
                              <Typography component="span" variant="body2" color="text.primary">
                                Size: {formatSize(file.size)}
                              </Typography>
                              <br />
                              <Typography component="span" variant="body2">
                                Uploaded: {formatDate(file.created_at)}
                              </Typography>
                              <br />
                              <Typography component="span" variant="body2">
                                {file.chunks && file.chunks.length > 0 ? 
                                  `Stored across ${file.chunks.length} chunks` : 
                                  'Storage information not available'}
                              </Typography>
                            </>
                          }
                        />
                      </ListItem>
                    </React.Fragment>
                  ))}
                </List>
              </Paper>
            </Box>
          )}
        </>
      )}

      <Dialog
        open={deleteConfirmOpen}
        onClose={handleDeleteCancel}
      >
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete "{selectedFile?.filename}"? This action cannot be undone.
          </DialogContentText>
          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} disabled={loading}>Cancel</Button>
          <Button 
            onClick={handleDeleteFile} 
            variant="contained" 
            color="error"
            disabled={loading}
          >
            {loading ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FileList; 