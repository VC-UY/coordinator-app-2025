import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Snackbar,
  Alert,
  Tab,
  Tabs,
  Badge,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Computer as ComputerIcon,
  Person as PersonIcon,
  Block as BlockIcon,
  PlayArrow as PlayArrowIcon,
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { MaterialReactTable } from 'material-react-table';
import AxiosInstance from './axios';

function ClientMonitoring() {
  const [tabValue, setTabValue] = useState(0);
  const [managers, setManagers] = useState([]);
  const [volunteers, setVolunteers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [detailsDialog, setDetailsDialog] = useState({ open: false, client: null, type: null });
  const [actionDialog, setActionDialog] = useState({ open: false, client: null, action: null, type: null });
  const [reason, setReason] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const [managersRes, volunteersRes] = await Promise.all([
        AxiosInstance.get('manager/'),
        AxiosInstance.get('volunteer/')
      ]);
      setManagers(managersRes.data);
      setVolunteers(volunteersRes.data);
    } catch (error) {
      console.error('Erreur lors du chargement des données:', error);
      showSnackbar('Erreur lors du chargement des données', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleActivate = async (client, type) => {
    try {
      const endpoint = type === 'manager' ? `manager/${client.id}/activate/` : `volunteer/${client.id}/activate/`;
      await AxiosInstance.post(endpoint);
      showSnackbar(`${type === 'manager' ? 'Manager' : 'Volunteer'} activé avec succès`, 'success');
      fetchData();
      setActionDialog({ open: false, client: null, action: null, type: null });
    } catch (error) {
      console.error('Erreur lors de l\'activation:', error);
      showSnackbar(error.response?.data?.message || 'Erreur lors de l\'activation', 'error');
    }
  };

  const handleDeactivate = async (client, type) => {
    try {
      const endpoint = type === 'manager' ? `manager/${client.id}/deactivate/` : `volunteer/${client.id}/deactivate/`;
      await AxiosInstance.post(endpoint, { reason });
      showSnackbar(`${type === 'manager' ? 'Manager' : 'Volunteer'} désactivé avec succès`, 'success');
      fetchData();
      setActionDialog({ open: false, client: null, action: null, type: null });
      setReason('');
    } catch (error) {
      console.error('Erreur lors de la désactivation:', error);
      showSnackbar(error.response?.data?.message || 'Erreur lors de la désactivation', 'error');
    }
  };

  const handleSuspend = async (client) => {
    try {
      await AxiosInstance.post(`manager/${client.id}/suspend/`, { reason });
      showSnackbar('Manager suspendu avec succès', 'success');
      fetchData();
      setActionDialog({ open: false, client: null, action: null, type: null });
      setReason('');
    } catch (error) {
      console.error('Erreur lors de la suspension:', error);
      showSnackbar(error.response?.data?.message || 'Erreur lors de la suspension', 'error');
    }
  };

  const handleActionConfirm = () => {
    const { client, action, type } = actionDialog;
    if (action === 'activate') {
      handleActivate(client, type);
    } else if (action === 'deactivate') {
      handleDeactivate(client, type);
    } else if (action === 'suspend') {
      handleSuspend(client);
    }
  };

  const getStatusChip = (status) => {
    const statusConfig = {
      active: { color: 'success', label: 'Actif', icon: <CheckCircleIcon /> },
      inactive: { color: 'default', label: 'Inactif', icon: <CancelIcon /> },
      suspended: { color: 'error', label: 'Suspendu', icon: <BlockIcon /> },
      available: { color: 'success', label: 'Disponible', icon: <CheckCircleIcon /> },
      busy: { color: 'warning', label: 'Occupé', icon: <ComputerIcon /> },
      offline: { color: 'default', label: 'Hors ligne', icon: <CancelIcon /> }
    };
    const config = statusConfig[status] || { color: 'default', label: status, icon: null };
    return <Chip icon={config.icon} label={config.label} color={config.color} size="small" />;
  };

  const managerColumns = useMemo(() => [
    {
      accessorKey: 'username',
      header: 'Nom d\'utilisateur',
      size: 150
    },
    {
      accessorKey: 'email',
      header: 'Email',
      size: 200
    },
    {
      accessorKey: 'first_name',
      header: 'Prénom',
      size: 150
    },
    {
      accessorKey: 'last_name',
      header: 'Nom',
      size: 150
    },
    {
      accessorKey: 'status',
      header: 'Statut',
      size: 120,
      Cell: ({ cell }) => getStatusChip(cell.getValue())
    },
    {
      accessorKey: 'registration_date',
      header: 'Date d\'inscription',
      size: 180,
      Cell: ({ cell }) => new Date(cell.getValue()).toLocaleString('fr-FR')
    },
    {
      accessorKey: 'last_login',
      header: 'Dernière connexion',
      size: 180,
      Cell: ({ cell }) => cell.getValue() ? new Date(cell.getValue()).toLocaleString('fr-FR') : 'Jamais'
    }
  ], []);

  const volunteerColumns = useMemo(() => [
    {
      accessorKey: 'name',
      header: 'Nom',
      size: 150
    },
    {
      accessorKey: 'username',
      header: 'Nom d\'utilisateur',
      size: 150
    },
    {
      accessorKey: 'is_active',
      header: 'État du compte',
      size: 120,
      Cell: ({ cell }) => cell.getValue() ?
        <Chip icon={<CheckCircleIcon />} label="Actif" color="success" size="small" /> :
        <Chip icon={<BlockIcon />} label="Désactivé" color="error" size="small" />
    },
    {
      accessorKey: 'current_status',
      header: 'Statut opérationnel',
      size: 150,
      Cell: ({ cell }) => getStatusChip(cell.getValue())
    },
    {
      accessorKey: 'cpu_model',
      header: 'Processeur',
      size: 200
    },
    {
      accessorKey: 'cpu_cores',
      header: 'Cœurs',
      size: 80
    },
    {
      accessorKey: 'total_ram',
      header: 'RAM (MB)',
      size: 100
    },
    {
      accessorKey: 'operating_system',
      header: 'OS',
      size: 150
    },
    {
      accessorKey: 'ip_address',
      header: 'Adresse IP',
      size: 130
    },
    {
      accessorKey: 'last_activity',
      header: 'Dernière activité',
      size: 180,
      Cell: ({ cell }) => cell.getValue() ? new Date(cell.getValue()).toLocaleString('fr-FR') : 'Jamais'
    }
  ], []);

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          <PersonIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Monitoring des Clients
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchData}
        >
          Actualiser
        </Button>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab
            label={
              <Badge badgeContent={managers.length} color="primary">
                Managers
              </Badge>
            }
          />
          <Tab
            label={
              <Badge badgeContent={volunteers.length} color="primary">
                Volunteers
              </Badge>
            }
          />
        </Tabs>
      </Box>

      {tabValue === 0 && (
        <Card>
          <CardContent>
            <MaterialReactTable
              columns={managerColumns}
              data={managers}
              enableRowActions
              positionActionsColumn="last"
              renderRowActions={({ row }) => (
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <IconButton
                    size="small"
                    color="info"
                    onClick={() => setDetailsDialog({ open: true, client: row.original, type: 'manager' })}
                  >
                    <VisibilityIcon />
                  </IconButton>
                  {row.original.status === 'active' ? (
                    <>
                      <Button
                        size="small"
                        variant="outlined"
                        color="warning"
                        onClick={() => setActionDialog({ open: true, client: row.original, action: 'deactivate', type: 'manager' })}
                      >
                        Désactiver
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        color="error"
                        onClick={() => setActionDialog({ open: true, client: row.original, action: 'suspend', type: 'manager' })}
                      >
                        Suspendre
                      </Button>
                    </>
                  ) : (
                    <Button
                      size="small"
                      variant="outlined"
                      color="success"
                      startIcon={<PlayArrowIcon />}
                      onClick={() => setActionDialog({ open: true, client: row.original, action: 'activate', type: 'manager' })}
                    >
                      Activer
                    </Button>
                  )}
                </Box>
              )}
              state={{ isLoading: loading }}
              initialState={{
                pagination: { pageSize: 10, pageIndex: 0 },
                sorting: [{ id: 'registration_date', desc: true }]
              }}
              muiTablePaperProps={{
                elevation: 0,
                sx: { border: 'none' }
              }}
            />
          </CardContent>
        </Card>
      )}

      {tabValue === 1 && (
        <Card>
          <CardContent>
            <MaterialReactTable
              columns={volunteerColumns}
              data={volunteers}
              enableRowActions
              positionActionsColumn="last"
              renderRowActions={({ row }) => (
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <IconButton
                    size="small"
                    color="info"
                    onClick={() => setDetailsDialog({ open: true, client: row.original, type: 'volunteer' })}
                  >
                    <VisibilityIcon />
                  </IconButton>
                  {row.original.is_active ? (
                    <Button
                      size="small"
                      variant="outlined"
                      color="error"
                      onClick={() => setActionDialog({ open: true, client: row.original, action: 'deactivate', type: 'volunteer' })}
                    >
                      Désactiver
                    </Button>
                  ) : (
                    <Button
                      size="small"
                      variant="outlined"
                      color="success"
                      startIcon={<PlayArrowIcon />}
                      onClick={() => setActionDialog({ open: true, client: row.original, action: 'activate', type: 'volunteer' })}
                    >
                      Activer
                    </Button>
                  )}
                </Box>
              )}
              state={{ isLoading: loading }}
              initialState={{
                pagination: { pageSize: 10, pageIndex: 0 },
                sorting: [{ id: 'last_activity', desc: true }]
              }}
              muiTablePaperProps={{
                elevation: 0,
                sx: { border: 'none' }
              }}
            />
          </CardContent>
        </Card>
      )}

      {/* Details Dialog */}
      <Dialog
        open={detailsDialog.open}
        onClose={() => setDetailsDialog({ open: false, client: null, type: null })}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">
              Détails du {detailsDialog.type === 'manager' ? 'Manager' : 'Volunteer'}
            </Typography>
            <IconButton onClick={() => setDetailsDialog({ open: false, client: null, type: null })}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          {detailsDialog.client && (
            <Grid container spacing={2}>
              {detailsDialog.type === 'manager' ? (
                <>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">Nom d'utilisateur</Typography>
                    <Typography variant="body1">{detailsDialog.client.username}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">Email</Typography>
                    <Typography variant="body1">{detailsDialog.client.email}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">Prénom</Typography>
                    <Typography variant="body1">{detailsDialog.client.first_name || 'N/A'}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">Nom</Typography>
                    <Typography variant="body1">{detailsDialog.client.last_name || 'N/A'}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">Statut</Typography>
                    {getStatusChip(detailsDialog.client.status)}
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">Date d'inscription</Typography>
                    <Typography variant="body1">
                      {new Date(detailsDialog.client.registration_date).toLocaleString('fr-FR')}
                    </Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary">Dernière connexion</Typography>
                    <Typography variant="body1">
                      {detailsDialog.client.last_login
                        ? new Date(detailsDialog.client.last_login).toLocaleString('fr-FR')
                        : 'Jamais'}
                    </Typography>
                  </Grid>
                </>
              ) : (
                <>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">Nom</Typography>
                    <Typography variant="body1">{detailsDialog.client.name}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">Nom d'utilisateur</Typography>
                    <Typography variant="body1">{detailsDialog.client.username}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">État du compte</Typography>
                    {detailsDialog.client.is_active ?
                      <Chip icon={<CheckCircleIcon />} label="Actif" color="success" size="small" /> :
                      <Chip icon={<BlockIcon />} label="Désactivé" color="error" size="small" />
                    }
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">Statut opérationnel</Typography>
                    {getStatusChip(detailsDialog.client.current_status)}
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>Spécifications techniques</Typography>
                    <Card variant="outlined">
                      <CardContent>
                        <Grid container spacing={1}>
                          <Grid item xs={12}>
                            <Typography variant="body2"><strong>CPU:</strong> {detailsDialog.client.cpu_model} ({detailsDialog.client.cpu_cores} cœurs)</Typography>
                          </Grid>
                          <Grid item xs={12}>
                            <Typography variant="body2"><strong>RAM:</strong> {detailsDialog.client.total_ram} MB</Typography>
                          </Grid>
                          <Grid item xs={12}>
                            <Typography variant="body2"><strong>Stockage:</strong> {detailsDialog.client.available_storage} GB</Typography>
                          </Grid>
                          <Grid item xs={12}>
                            <Typography variant="body2"><strong>OS:</strong> {detailsDialog.client.operating_system}</Typography>
                          </Grid>
                          <Grid item xs={12}>
                            <Typography variant="body2">
                              <strong>GPU:</strong> {detailsDialog.client.gpu_available
                                ? `${detailsDialog.client.gpu_model} (${detailsDialog.client.gpu_memory} MB)`
                                : 'Non disponible'}
                            </Typography>
                          </Grid>
                        </Grid>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">Adresse IP</Typography>
                    <Typography variant="body1">{detailsDialog.client.ip_address}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" color="text.secondary">Port</Typography>
                    <Typography variant="body1">{detailsDialog.client.communication_port}</Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary">Dernière activité</Typography>
                    <Typography variant="body1">
                      {detailsDialog.client.last_activity
                        ? new Date(detailsDialog.client.last_activity).toLocaleString('fr-FR')
                        : 'Jamais'}
                    </Typography>
                  </Grid>
                </>
              )}
            </Grid>
          )}
        </DialogContent>
      </Dialog>

      {/* Action Confirmation Dialog */}
      <Dialog
        open={actionDialog.open}
        onClose={() => {
          setActionDialog({ open: false, client: null, action: null, type: null });
          setReason('');
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Confirmer l'action
        </DialogTitle>
        <DialogContent>
          {actionDialog.client && (
            <>
              <Typography gutterBottom>
                Êtes-vous sûr de vouloir {' '}
                {actionDialog.action === 'activate' && 'activer'}
                {actionDialog.action === 'deactivate' && 'désactiver'}
                {actionDialog.action === 'suspend' && 'suspendre'}
                {' '} {actionDialog.type === 'manager' ? 'le manager' : 'le volunteer'} {' '}
                <strong>{actionDialog.client.username || actionDialog.client.name}</strong> ?
              </Typography>
              {(actionDialog.action === 'deactivate' || actionDialog.action === 'suspend') && (
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Raison (optionnel)"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  sx={{ mt: 2 }}
                />
              )}
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setActionDialog({ open: false, client: null, action: null, type: null });
              setReason('');
            }}
          >
            Annuler
          </Button>
          <Button
            onClick={handleActionConfirm}
            variant="contained"
            color={actionDialog.action === 'activate' ? 'success' : 'error'}
          >
            Confirmer
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default ClientMonitoring;
