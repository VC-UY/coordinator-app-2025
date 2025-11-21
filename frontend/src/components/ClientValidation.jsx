import React, { useEffect, useState, useMemo } from 'react';
import {
  Box, Typography, Paper, Grid, Card, CardContent, Tabs, Tab,
  IconButton, Chip, Button, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, Alert, Snackbar, LinearProgress,
  List, ListItem, ListItemText, ListItemSecondaryAction, Tooltip
} from '@mui/material';
import { MaterialReactTable } from 'material-react-table';
import SecurityIcon from '@mui/icons-material/Security';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import BlockIcon from '@mui/icons-material/Block';
import WarningIcon from '@mui/icons-material/Warning';
import PersonOffIcon from '@mui/icons-material/PersonOff';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import RefreshIcon from '@mui/icons-material/Refresh';
import InfoIcon from '@mui/icons-material/Info';
import DeleteIcon from '@mui/icons-material/Delete';
import AxiosInstance from './axios';

const ClientValidation = () => {
  const [tabValue, setTabValue] = useState(0);
  const [stats, setStats] = useState(null);
  const [registrations, setRegistrations] = useState([]);
  const [loginAttempts, setLoginAttempts] = useState([]);
  const [securityAlerts, setSecurityAlerts] = useState([]);
  const [ipBlacklist, setIpBlacklist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogType, setDialogType] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  // Fetch all data
  const fetchData = async () => {
    try {
      setLoading(true);
      const [statsData, regsData, attemptsData, alertsData, blacklistData] = await Promise.all([
        AxiosInstance.get('api/validation/stats/'),
        AxiosInstance.get('api/registrations/'),
        AxiosInstance.get('api/login-attempts/'),
        AxiosInstance.get('api/security-alerts/'),
        AxiosInstance.get('api/ip-blacklist/')
      ]);

      setStats(statsData.data);
      setRegistrations(regsData.data);
      setLoginAttempts(attemptsData.data);
      setSecurityAlerts(alertsData.data);
      setIpBlacklist(blacklistData.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      showSnackbar('Erreur lors du chargement des données', 'error');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Approve registration
  const handleApprove = async (registration) => {
    try {
      await AxiosInstance.post(`api/registrations/${registration.id}/approve/`);
      showSnackbar('Inscription approuvée avec succès', 'success');
      fetchData();
    } catch (error) {
      console.error('Error approving registration:', error);
      showSnackbar('Erreur lors de l\'approbation', 'error');
    }
  };

  // Reject registration
  const handleReject = async (registration, reason) => {
    try {
      await AxiosInstance.post(`api/registrations/${registration.id}/reject/`, { reason });
      showSnackbar('Inscription rejetée', 'warning');
      setDialogOpen(false);
      setRejectReason('');
      fetchData();
    } catch (error) {
      console.error('Error rejecting registration:', error);
      showSnackbar('Erreur lors du rejet', 'error');
    }
  };

  // Resolve security alert
  const handleResolveAlert = async (alert, notes) => {
    try {
      await AxiosInstance.post(`api/security-alerts/${alert.id}/resolve/`, { notes });
      showSnackbar('Alerte résolue', 'success');
      setDialogOpen(false);
      fetchData();
    } catch (error) {
      console.error('Error resolving alert:', error);
      showSnackbar('Erreur lors de la résolution', 'error');
    }
  };

  // Remove IP from blacklist
  const handleRemoveIP = async (entry) => {
    try {
      await AxiosInstance.delete(`api/ip-blacklist/${entry.id}/`);
      showSnackbar('IP retirée de la liste noire', 'success');
      fetchData();
    } catch (error) {
      console.error('Error removing IP:', error);
      showSnackbar('Erreur lors du retrait de l\'IP', 'error');
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      'low': 'info',
      'medium': 'warning',
      'high': 'error',
      'critical': 'error'
    };
    return colors[severity] || 'default';
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending': 'warning',
      'approved': 'success',
      'rejected': 'error',
      'success': 'success',
      'failed': 'error',
      'blocked': 'error'
    };
    return colors[status] || 'default';
  };

  // Statistics Cards
  const StatCard = ({ title, value, subtitle, icon, color }) => (
    <Card sx={{ height: '100%', background: `linear-gradient(135deg, ${color}15 0%, ${color}05 100%)` }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700, color }}>
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="caption" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box sx={{ color, opacity: 0.3 }}>
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  // Registrations Table
  const registrationsColumns = useMemo(() => [
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
      accessorKey: 'client_type',
      header: 'Type',
      size: 100,
      Cell: ({ cell }) => (
        <Chip
          label={cell.getValue() === 'manager' ? 'Manager' : 'Volontaire'}
          size="small"
          color={cell.getValue() === 'manager' ? 'primary' : 'secondary'}
        />
      )
    },
    {
      accessorKey: 'validation_status',
      header: 'Statut',
      size: 120,
      Cell: ({ cell }) => (
        <Chip
          label={cell.getValue()}
          color={getStatusColor(cell.getValue())}
          size="small"
        />
      )
    },
    {
      accessorKey: 'ip_address',
      header: 'IP',
      size: 120
    },
    {
      accessorKey: 'registration_date',
      header: 'Date',
      size: 150,
      Cell: ({ cell }) => new Date(cell.getValue()).toLocaleString('fr-FR')
    },
    {
      accessorKey: 'actions',
      header: 'Actions',
      size: 150,
      Cell: ({ row }) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {row.original.validation_status === 'pending' && (
            <>
              <Tooltip title="Approuver">
                <IconButton
                  size="small"
                  color="success"
                  onClick={() => handleApprove(row.original)}
                >
                  <CheckCircleIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Rejeter">
                <IconButton
                  size="small"
                  color="error"
                  onClick={() => {
                    setSelectedItem(row.original);
                    setDialogType('reject');
                    setDialogOpen(true);
                  }}
                >
                  <CancelIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </>
          )}
          <Tooltip title="Détails">
            <IconButton
              size="small"
              color="info"
              onClick={() => {
                setSelectedItem(row.original);
                setDialogType('details');
                setDialogOpen(true);
              }}
            >
              <InfoIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      )
    }
  ], []);

  // Login Attempts Table
  const attemptsColumns = useMemo(() => [
    {
      accessorKey: 'username',
      header: 'Utilisateur',
      size: 150
    },
    {
      accessorKey: 'ip_address',
      header: 'IP',
      size: 120
    },
    {
      accessorKey: 'status',
      header: 'Statut',
      size: 100,
      Cell: ({ cell }) => (
        <Chip
          label={cell.getValue()}
          color={getStatusColor(cell.getValue())}
          size="small"
        />
      )
    },
    {
      accessorKey: 'timestamp',
      header: 'Date/Heure',
      size: 150,
      Cell: ({ cell }) => new Date(cell.getValue()).toLocaleString('fr-FR')
    },
    {
      accessorKey: 'failure_reason',
      header: 'Raison',
      size: 200
    },
    {
      accessorKey: 'is_suspicious',
      header: 'Suspect',
      size: 80,
      Cell: ({ cell }) => cell.getValue() ? (
        <WarningIcon color="warning" fontSize="small" />
      ) : null
    }
  ], []);

  // Security Alerts Table
  const alertsColumns = useMemo(() => [
    {
      accessorKey: 'alert_type',
      header: 'Type',
      size: 150,
      Cell: ({ cell }) => (
        <Chip label={cell.getValue()} size="small" />
      )
    },
    {
      accessorKey: 'severity',
      header: 'Sévérité',
      size: 100,
      Cell: ({ cell }) => (
        <Chip
          label={cell.getValue().toUpperCase()}
          color={getSeverityColor(cell.getValue())}
          size="small"
        />
      )
    },
    {
      accessorKey: 'title',
      header: 'Titre',
      size: 200
    },
    {
      accessorKey: 'ip_address',
      header: 'IP',
      size: 120
    },
    {
      accessorKey: 'timestamp',
      header: 'Date/Heure',
      size: 150,
      Cell: ({ cell }) => new Date(cell.getValue()).toLocaleString('fr-FR')
    },
    {
      accessorKey: 'is_resolved',
      header: 'Résolu',
      size: 80,
      Cell: ({ cell }) => cell.getValue() ? (
        <CheckCircleIcon color="success" fontSize="small" />
      ) : (
        <ErrorIcon color="error" fontSize="small" />
      )
    },
    {
      accessorKey: 'actions',
      header: 'Actions',
      size: 100,
      Cell: ({ row }) => (
        !row.original.is_resolved && (
          <Tooltip title="Résoudre">
            <IconButton
              size="small"
              color="success"
              onClick={() => {
                setSelectedItem(row.original);
                setDialogType('resolve');
                setDialogOpen(true);
              }}
            >
              <CheckCircleIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )
      )
    }
  ], []);

  // IP Blacklist Table
  const blacklistColumns = useMemo(() => [
    {
      accessorKey: 'ip_address',
      header: 'Adresse IP',
      size: 150
    },
    {
      accessorKey: 'reason',
      header: 'Raison',
      size: 250
    },
    {
      accessorKey: 'blocked_at',
      header: 'Bloqué le',
      size: 150,
      Cell: ({ cell }) => new Date(cell.getValue()).toLocaleString('fr-FR')
    },
    {
      accessorKey: 'is_permanent',
      header: 'Permanent',
      size: 100,
      Cell: ({ cell }) => (
        <Chip
          label={cell.getValue() ? 'Permanent' : 'Temporaire'}
          color={cell.getValue() ? 'error' : 'warning'}
          size="small"
        />
      )
    },
    {
      accessorKey: 'expires_at',
      header: 'Expire le',
      size: 150,
      Cell: ({ cell }) => cell.getValue() ? new Date(cell.getValue()).toLocaleString('fr-FR') : '-'
    },
    {
      accessorKey: 'actions',
      header: 'Actions',
      size: 100,
      Cell: ({ row }) => (
        <Tooltip title="Retirer">
          <IconButton
            size="small"
            color="error"
            onClick={() => handleRemoveIP(row.original)}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      )
    }
  ], []);

  return (
    <Box sx={{ p: { xs: 2, md: 4 }, background: '#f5f6fa', minHeight: '100vh' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" fontWeight={700}>
          Validation et Sécurité des Clients
        </Typography>
        <IconButton onClick={fetchData} color="primary">
          <RefreshIcon />
        </IconButton>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Statistics Cards */}
      {stats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Tentatives de connexion"
              value={stats.login_attempts.total}
              subtitle={`Taux de réussite: ${stats.login_attempts.success_rate}%`}
              icon={<PersonAddIcon sx={{ fontSize: 40 }} />}
              color="#002060"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Inscriptions en attente"
              value={stats.registrations.pending}
              subtitle={`${stats.registrations.approved} approuvées`}
              icon={<PersonOffIcon sx={{ fontSize: 40 }} />}
              color="#00B0F0"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="Alertes critiques"
              value={stats.security_alerts.critical}
              subtitle={`${stats.security_alerts.unresolved} non résolues`}
              icon={<WarningIcon sx={{ fontSize: 40 }} />}
              color="#ff9800"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard
              title="IPs bloquées"
              value={stats.blocked_ips}
              subtitle="Liste noire active"
              icon={<BlockIcon sx={{ fontSize: 40 }} />}
              color="#f44336"
            />
          </Grid>
        </Grid>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 2 }}>
        <Tabs value={tabValue} onChange={(e, val) => setTabValue(val)}>
          <Tab label="Inscriptions" />
          <Tab label="Tentatives de connexion" />
          <Tab label="Alertes de sécurité" />
          <Tab label="Liste noire IP" />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <Paper sx={{ p: 2 }}>
        {tabValue === 0 && (
          <MaterialReactTable
            columns={registrationsColumns}
            data={registrations}
            enableStickyHeader
            initialState={{
              sorting: [{ id: 'registration_date', desc: true }]
            }}
          />
        )}

        {tabValue === 1 && (
          <MaterialReactTable
            columns={attemptsColumns}
            data={loginAttempts}
            enableStickyHeader
            initialState={{
              sorting: [{ id: 'timestamp', desc: true }]
            }}
          />
        )}

        {tabValue === 2 && (
          <MaterialReactTable
            columns={alertsColumns}
            data={securityAlerts}
            enableStickyHeader
            initialState={{
              sorting: [{ id: 'timestamp', desc: true }]
            }}
          />
        )}

        {tabValue === 3 && (
          <MaterialReactTable
            columns={blacklistColumns}
            data={ipBlacklist}
            enableStickyHeader
            initialState={{
              sorting: [{ id: 'blocked_at', desc: true }]
            }}
          />
        )}
      </Paper>

      {/* Dialogs */}
      {/* Reject Dialog */}
      <Dialog open={dialogOpen && dialogType === 'reject'} onClose={() => setDialogOpen(false)}>
        <DialogTitle>Rejeter l'inscription</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Raison du rejet"
            fullWidth
            multiline
            rows={3}
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Annuler</Button>
          <Button
            onClick={() => handleReject(selectedItem, rejectReason)}
            color="error"
            variant="contained"
          >
            Rejeter
          </Button>
        </DialogActions>
      </Dialog>

      {/* Resolve Alert Dialog */}
      <Dialog open={dialogOpen && dialogType === 'resolve'} onClose={() => setDialogOpen(false)}>
        <DialogTitle>Résoudre l'alerte</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Notes de résolution"
            fullWidth
            multiline
            rows={3}
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Annuler</Button>
          <Button
            onClick={() => handleResolveAlert(selectedItem, rejectReason)}
            color="success"
            variant="contained"
          >
            Résoudre
          </Button>
        </DialogActions>
      </Dialog>

      {/* Details Dialog */}
      <Dialog open={dialogOpen && dialogType === 'details'} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Détails de l'inscription</DialogTitle>
        <DialogContent dividers>
          {selectedItem && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">Nom d'utilisateur</Typography>
                  <Typography variant="body1">{selectedItem.username}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">Email</Typography>
                  <Typography variant="body1">{selectedItem.email}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">Type de client</Typography>
                  <Typography variant="body1">{selectedItem.client_type}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">Adresse IP</Typography>
                  <Typography variant="body1">{selectedItem.ip_address}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">Email valide</Typography>
                  <Chip
                    label={selectedItem.email_valid ? 'Oui' : 'Non'}
                    color={selectedItem.email_valid ? 'success' : 'error'}
                    size="small"
                  />
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">Score de réputation IP</Typography>
                  <Typography variant="body1">{selectedItem.ip_reputation_score}/100</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">Force du mot de passe</Typography>
                  <Typography variant="body1">{selectedItem.password_strength_score}/5</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">Vérification doublons</Typography>
                  <Chip
                    label={selectedItem.duplicate_check_passed ? 'Passé' : 'Échec'}
                    color={selectedItem.duplicate_check_passed ? 'success' : 'error'}
                    size="small"
                  />
                </Grid>
                {selectedItem.rejection_reason && (
                  <Grid item xs={12}>
                    <Alert severity="error">
                      <Typography variant="subtitle2">Raison du rejet</Typography>
                      <Typography variant="body2">{selectedItem.rejection_reason}</Typography>
                    </Alert>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Fermer</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ClientValidation;
