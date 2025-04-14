import React from 'react';
import {
  Typography,
  Box,
  Card,
  CardContent,
  Grid,
  LinearProgress,
  Chip,
  Divider,
  Link,
  Tooltip
} from '@mui/material';
import StorageIcon from '@mui/icons-material/Storage';
import SpeedIcon from '@mui/icons-material/Speed';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';

function NodeStatus({ nodes }) {
  const getUsagePercentage = (node) => {
    if (!node.limit_mb || !node.used_mb) return 0;
    return Math.min(100, Math.round((node.used_mb / node.limit_mb) * 100));
  };

  const getUsageColor = (percentage) => {
    if (percentage < 60) return 'success';
    if (percentage < 85) return 'warning';
    return 'error';
  };

  const formatStorage = (mb) => {
    if (!mb) return '0 MB';
    if (mb < 1024) return `${Math.round(mb * 10) / 10} MB`;
    return `${Math.round((mb / 1024) * 10) / 10} GB`;
  };

  const shortenAddress = (address) => {
    if (!address) return 'Not connected';
    return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
  };

  return (
    <Box>
      <Typography variant="h5" component="h2" gutterBottom>
        Storage Network
      </Typography>
      
      {nodes.length === 0 ? (
        <Typography variant="body1" color="textSecondary" sx={{ my: 4, textAlign: 'center' }}>
          No storage nodes are currently available in the network.
        </Typography>
      ) : (
        <Grid container spacing={3}>
          {nodes.map((node) => {
            const usagePercent = getUsagePercentage(node);
            return (
              <Grid item xs={12} md={6} key={node.node_id}>
                <Card 
                  variant="outlined" 
                  sx={{ 
                    height: '100%',
                    transition: 'transform 0.2s ease-in-out',
                    '&:hover': {
                      transform: 'translateY(-5px)',
                      boxShadow: 3
                    }
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <StorageIcon fontSize="large" color="primary" sx={{ mr: 1 }} />
                      <Typography variant="h6" component="div">
                        Node {node.node_id}
                      </Typography>
                      <Box sx={{ flexGrow: 1 }} />
                      <Chip 
                        label={usagePercent < 90 ? "Available" : "Near Capacity"} 
                        color={usagePercent < 90 ? "success" : "warning"} 
                        size="small" 
                      />
                    </Box>
                    
                    <Divider sx={{ my: 1.5 }} />
                    
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Storage Usage
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                        <Box sx={{ flexGrow: 1, mr: 1 }}>
                          <LinearProgress 
                            variant="determinate" 
                            value={usagePercent} 
                            color={getUsageColor(usagePercent)}
                            sx={{ height: 8, borderRadius: 5 }}
                          />
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          {usagePercent}%
                        </Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        {formatStorage(node.used_mb)} used of {formatStorage(node.limit_mb)}
                      </Typography>
                    </Box>
                    
                    <Grid container spacing={2}>
                      {node.price_per_mb && (
                        <Grid item xs={6}>
                          <Tooltip title="Cost per MB per day">
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <SpeedIcon fontSize="small" color="action" sx={{ mr: 1 }} />
                              <Typography variant="body2">
                                {node.price_per_mb} wei/MB/day
                              </Typography>
                            </Box>
                          </Tooltip>
                        </Grid>
                      )}
                      
                      {node.wallet_address && (
                        <Grid item xs={6}>
                          <Tooltip title="Node wallet address">
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <AccountBalanceWalletIcon fontSize="small" color="action" sx={{ mr: 1 }} />
                              <Typography variant="body2" sx={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                <Link 
                                  href={`https://etherscan.io/address/${node.wallet_address}`} 
                                  target="_blank" 
                                  rel="noopener"
                                  underline="hover"
                                  color="inherit"
                                >
                                  {shortenAddress(node.wallet_address)}
                                </Link>
                              </Typography>
                            </Box>
                          </Tooltip>
                        </Grid>
                      )}
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="textSecondary">
          Total Network Capacity: {formatStorage(nodes.reduce((sum, node) => sum + (node.limit_mb || 0), 0))}
        </Typography>
        <Typography variant="body2" color="textSecondary">
          Available: {formatStorage(
            nodes.reduce((sum, node) => sum + (node.limit_mb || 0) - (node.used_mb || 0), 0)
          )}
        </Typography>
      </Box>
    </Box>
  );
}

export default NodeStatus; 