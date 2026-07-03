import React, { useEffect, useState, useMemo, useRef } from 'react';
import {
  Box, Typography, CircularProgress, Chip, Paper, IconButton, Tooltip,
  Dialog, DialogTitle, DialogContent, DialogActions, Button, Alert,
  TextField, Select, MenuItem, FormControl, InputLabel, Snackbar, List, ListItem, ListItemText
} from '@mui/material';
import { MaterialReactTable } from 'material-react-table';
import AssignmentIcon from '@mui/icons-material/Assignment';
import RefreshIcon from '@mui/icons-material/Refresh';
import PersonIcon from '@mui/icons-material/Person';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import StopIcon from '@mui/icons-material/Stop';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import InfoIcon from '@mui/icons-material/Info';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import AxiosInstance from './axios';

const Tasks = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [selectedTask, setSelectedTask] = useState(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [dependenciesDialogOpen, setDependenciesDialogOpen] = useState(false);
  const [dependencies, setDependencies] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [wsConnected, setWsConnected] = useState(false);

  const wsRef = useRef(null);

  // Form states for editing
  const [editForm, setEditForm] = useState({
    name: '',
    description: '',
    status: '',
    progress: 0
  });

  // WebSocket connection
  useEffect(() => {
    // Connexion WebSocket pour les mises à jour en temps réel
    const connectWebSocket = () => {
      // Déterminer l'URL WebSocket en fonction de l'environnement
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = import.meta.env.PROD ? window.location.host : 'localhost:8001';
      const wsUrl = `${wsProtocol}//${wsHost}/ws/tasks/`;

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connecté');
        setWsConnected(true);
        showSnackbar('Connecté au système de mises à jour en temps réel', 'success');

        // S'abonner aux notifications de tâches
        ws.send(JSON.stringify({
          type: 'subscribe',
          topics: ['task_created', 'task_updated', 'task_deleted', 'task_stopped', 'task_resumed', 'task_status_changed']
        }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Message WebSocket reçu:', data);

          switch (data.type) {
            case 'connection_established':
            case 'subscription_confirmed':
              console.log(data.message);
              break;

            case 'task_created':
            case 'task_updated':
            case 'task_status_changed':
            case 'task_stopped':
            case 'task_resumed':
              // Rafraîchir les données
              fetchData();
              if (data.type !== 'connection_established') {
                showSnackbar(`Tâche mise à jour: ${data.task_name || 'Tâche'}`, 'info');
              }
              break;

            case 'task_deleted':
              fetchData();
              showSnackbar('Tâche supprimée', 'warning');
              break;

            default:
              console.log('Type de message inconnu:', data.type);
          }
        } catch (error) {
          console.error('Erreur lors du traitement du message WebSocket:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('Erreur WebSocket:', error);
        setWsConnected(false);
      };

      ws.onclose = () => {
        console.log('WebSocket déconnecté');
        setWsConnected(false);
        // Tenter de se reconnecter après 5 secondes
        setTimeout(connectWebSocket, 5000);
      };

      wsRef.current = ws;
    };

    connectWebSocket();

    // Cleanup lors du démontage
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const fetchData = async () => {
    try {
      const res = await AxiosInstance.get('tasks/');
      setTasks(res.data);
      setLoading(false);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error fetching tasks:', error);
      setTasks([]);
      setLoading(false);
      showSnackbar('Erreur lors du chargement des tâches', 'error');
    }
  };

  useEffect(() => {
    fetchData();
    // Polling de backup si WebSocket déconnecté
    const interval = setInterval(() => {
      if (!wsConnected) {
        fetchData();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [wsConnected]);

  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const getStatusColor = (status) => {
    const colors = {
      'CREATED': 'default',
      'ASSIGNED': 'info',
      'RUNNING': 'primary',
      'PAUSED': 'warning',
      'COMPLETED': 'success',
      'FAILED': 'error',
      'PENDING': 'secondary'
    };
    return colors[status] || 'default';
  };

  const getStatusLabel = (status) => {
    const labels = {
      'CREATED': 'Créée',
      'ASSIGNED': 'Assignée',
      'RUNNING': 'En cours',
      'PAUSED': 'En pause',
      'COMPLETED': 'Terminée',
      'FAILED': 'Échouée',
      'PENDING': 'En attente'
    };
    return labels[status] || status;
  };

  // Handle Edit
  const handleEditClick = (task) => {
    setSelectedTask(task);
    setEditForm({
      name: task.name,
      description: task.description || '',
      status: task.status,
      progress: task.progress || 0
    });
    setEditDialogOpen(true);
  };

  const handleEditSubmit = async () => {
    try {
      await AxiosInstance.patch(`tasks/${selectedTask.id}/`, editForm);
      showSnackbar('Tâche mise à jour avec succès', 'success');
      setEditDialogOpen(false);
      fetchData();
    } catch (error) {
      console.error('Error updating task:', error);
      showSnackbar('Erreur lors de la mise à jour de la tâche', 'error');
    }
  };

  // Handle Delete
  const handleDeleteClick = (task) => {
    setSelectedTask(task);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    try {
      await AxiosInstance.delete(`tasks/${selectedTask.id}/`);
      showSnackbar('Tâche supprimée avec succès', 'success');
      setDeleteDialogOpen(false);
      fetchData();
    } catch (error) {
      console.error('Error deleting task:', error);
      showSnackbar('Erreur lors de la suppression de la tâche', 'error');
    }
  };

  // Handle Stop
  const handleStop = async (task) => {
    try {
      await AxiosInstance.post(`tasks/${task.id}/stop/`);
      showSnackbar(`Tâche "${task.name}" arrêtée avec succès`, 'success');
      fetchData();
    } catch (error) {
      console.error('Error stopping task:', error);
      const message = error.response?.data?.message || 'Erreur lors de l\'arrêt de la tâche';
      showSnackbar(message, 'error');
    }
  };

  // Handle Resume
  const handleResume = async (task) => {
    try {
      await AxiosInstance.post(`tasks/${task.id}/resume/`);
      showSnackbar(`Tâche "${task.name}" reprise avec succès`, 'success');
      fetchData();
    } catch (error) {
      console.error('Error resuming task:', error);
      const message = error.response?.data?.message || 'Erreur lors de la reprise de la tâche';
      showSnackbar(message, 'error');
    }
  };

  // Handle Dependencies Check
  const handleCheckDependencies = async (task) => {
    try {
      const response = await AxiosInstance.get(`tasks/${task.id}/dependencies/`);
      setDependencies(response.data);
      setSelectedTask(task);
      setDependenciesDialogOpen(true);
    } catch (error) {
      console.error('Error checking dependencies:', error);
      showSnackbar('Erreur lors de la vérification des dépendances', 'error');
    }
  };

  // Handle Detail
  const handleDetailClick = (task) => {
    setSelectedTask(task);
    setDetailDialogOpen(true);
  };

  const columns = useMemo(
    () => [
      {
        accessorKey: 'name',
        header: 'Nom de la tâche',
        size: 200
      },
      {
        accessorKey: 'status',
        header: 'Statut',
        size: 120,
        Cell: ({ cell }) => (
          <Chip
            label={getStatusLabel(cell.getValue())}
            color={getStatusColor(cell.getValue())}
            size="small"
          />
        )
      },
      {
        accessorKey: 'workflow_name',
        header: 'Workflow',
        size: 180,
        Cell: ({ row }) => {
          const name = row.original.workflow_name || row.original.workflow;
          if (name) {
            return (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AccountTreeIcon sx={{ fontSize: 18, color: '#00B0F0' }} />
                <Typography sx={{ color: '#FFFFFF' }}>{name}</Typography>
              </Box>
            );
          }
          return <Typography sx={{ color: '#999' }}>-</Typography>;
        }
      },
      {
        accessorKey: 'owner_email',
        header: 'Manager',
        size: 160,
        Cell: ({ row }) => (
          <Typography sx={{ color: '#00B0F0', fontSize: '0.85rem' }}>
            {row.original.owner_email || row.original.owner_username || '—'}
          </Typography>
        )
      },
      {
        accessorKey: 'assigned_to_name',
        header: 'Volontaire',
        size: 150,
        Cell: ({ row }) => {
          const name = row.original.assigned_to_name || row.original.assigned_to;
          if (name && typeof name !== 'object') {
            return (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <PersonIcon sx={{ fontSize: 18, color: '#00D4FF' }} />
                <Typography sx={{ color: '#FFFFFF' }}>{name}</Typography>
              </Box>
            );
          }
          if (name && typeof name === 'object' && name.name) {
            return (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <PersonIcon sx={{ fontSize: 18, color: '#00D4FF' }} />
                <Typography sx={{ color: '#FFFFFF' }}>{name.name}</Typography>
              </Box>
            );
          }
          return <Typography sx={{ color: '#999' }}>Non assigné</Typography>;
        }
      },
      {
        accessorKey: 'progress',
        header: 'Progression',
        size: 100,
        Cell: ({ cell }) => `${cell.getValue() || 0}%`
      },
      {
        accessorKey: 'created_at',
        header: 'Créée le',
        size: 120,
        Cell: ({ cell }) => new Date(cell.getValue()).toLocaleDateString('fr-FR')
      },
      {
        accessorKey: 'actions',
        header: 'Actions',
        size: 250,
        Cell: ({ row }) => (
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <IconButton
              size="small"
              color="info"
              onClick={() => handleDetailClick(row.original)}
              title="Détails"
            >
              <InfoIcon fontSize="small" />
            </IconButton>
            <IconButton
              size="small"
              color="primary"
              onClick={() => handleEditClick(row.original)}
              title="Modifier"
            >
              <EditIcon fontSize="small" />
            </IconButton>
            <IconButton
              size="small"
              color="error"
              onClick={() => handleDeleteClick(row.original)}
              title="Supprimer"
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
            {['RUNNING', 'ASSIGNED'].includes(row.original.status) && (
              <IconButton
                size="small"
                color="warning"
                onClick={() => handleStop(row.original)}
                title="Arrêter"
              >
                <StopIcon fontSize="small" />
              </IconButton>
            )}
            {row.original.status === 'PAUSED' && (
              <IconButton
                size="small"
                color="success"
                onClick={() => handleResume(row.original)}
                title="Reprendre"
              >
                <PlayArrowIcon fontSize="small" />
              </IconButton>
            )}
            {row.original.dependencies && row.original.dependencies.length > 0 && (
              <IconButton
                size="small"
                color="secondary"
                onClick={() => handleCheckDependencies(row.original)}
                title="Dépendances"
              >
                <AccountTreeIcon fontSize="small" />
              </IconButton>
            )}
          </Box>
        )
      },
    ], []
  );

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)',
        p: { xs: 2, md: 4 }
      }}
    >
      <style>
        {`
          @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
          }

          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }

          @keyframes slideIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
          }
        `}
      </style>

      {/* Header Section */}
      <Paper
        elevation={0}
        sx={{
          background: 'linear-gradient(135deg, #002060 0%, #001440 100%)',
          borderRadius: '24px',
          p: 3,
          mb: 3,
          position: 'relative',
          overflow: 'hidden',
          animation: 'slideIn 0.6s ease-out'
        }}
      >
        <Box sx={{ position: 'relative', zIndex: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box
                sx={{
                  backgroundColor: '#00B0F0',
                  borderRadius: '16px',
                  p: 1.5,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <AssignmentIcon sx={{ color: 'white', fontSize: 32 }} />
              </Box>
              <Box>
                <Typography
                  variant='h4'
                  sx={{
                    fontWeight: 700,
                    color: 'white',
                    mb: 0.5
                  }}
                >
                  Gestion des Tâches
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip
                    label={wsConnected ? "Temps réel actif" : "Temps réel inactif"}
                    color={wsConnected ? "success" : "warning"}
                    size="small"
                    sx={{ fontSize: '0.75rem' }}
                  />
                  <Typography
                    variant='body2'
                    sx={{
                      color: '#00D4FF',
                      fontWeight: 500
                    }}
                  >
                    {tasks.length} tâche{tasks.length !== 1 ? 's' : ''}
                  </Typography>
                </Box>
              </Box>
            </Box>

            <Tooltip title="Actualiser">
              <IconButton
                onClick={fetchData}
                sx={{
                  backgroundColor: 'rgba(0,176,240,0.2)',
                  color: '#00D4FF',
                  '&:hover': {
                    backgroundColor: 'rgba(0,176,240,0.3)',
                  }
                }}
              >
                <RefreshIcon sx={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
              </IconButton>
            </Tooltip>
          </Box>

          <Box sx={{ display: 'flex', gap: 3, mt: 3 }}>
            <Box
              sx={{
                backgroundColor: 'rgba(0,176,240,0.15)',
                borderRadius: '16px',
                p: 2,
                flex: 1,
                border: '1px solid rgba(0,176,240,0.3)'
              }}
            >
              <Typography sx={{ color: '#00D4FF', fontSize: '0.875rem', mb: 1 }}>
                Total des tâches
              </Typography>
              <Typography sx={{ color: 'white', fontSize: '2rem', fontWeight: 700 }}>
                {tasks.length}
              </Typography>
            </Box>

            <Box
              sx={{
                backgroundColor: 'rgba(0,212,255,0.15)',
                borderRadius: '16px',
                p: 2,
                flex: 1,
                border: '1px solid rgba(0,212,255,0.3)'
              }}
            >
              <Typography sx={{ color: '#00D4FF', fontSize: '0.875rem', mb: 1 }}>
                Dernière mise à jour
              </Typography>
              <Typography sx={{ color: 'white', fontSize: '1rem', fontWeight: 600 }}>
                {lastUpdate.toLocaleTimeString('fr-FR')}
              </Typography>
            </Box>
          </Box>
        </Box>
      </Paper>

      {/* Table Section */}
      <Paper
        elevation={0}
        sx={{
          borderRadius: '24px',
          overflow: 'hidden',
          animation: 'slideIn 0.8s ease-out',
          border: '1px solid rgba(0,32,96,0.1)'
        }}
      >
        {loading && tasks.length === 0 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
            <CircularProgress sx={{ color: '#00B0F0' }} />
          </Box>
        ) : tasks.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <AssignmentIcon sx={{ fontSize: 64, color: '#00B0F0', mb: 2, opacity: 0.5 }} />
            <Typography sx={{ color: '#001440', fontSize: '1.25rem', fontWeight: 600 }}>
              Aucune tâche disponible
            </Typography>
            <Typography sx={{ color: '#666', mt: 1 }}>
              Les tâches apparaîtront ici une fois créées
            </Typography>
          </Box>
        ) : (
          <MaterialReactTable
            columns={columns}
            data={tasks}
            enableColumnResizing
            enableStickyHeader
            muiTablePaperProps={{
              elevation: 0,
              sx: { borderRadius: 0 }
            }}
            muiTableHeadCellProps={{
              sx: {
                backgroundColor: '#002060',
                color: 'white',
                fontWeight: 700,
                fontSize: '0.875rem',
                borderBottom: '2px solid #00B0F0',
                py: 2
              }
            }}
            muiTableBodyCellProps={{
              sx: {
                borderBottom: '1px solid rgba(0,32,96,0.08)',
                py: 2
              }
            }}
            muiTableBodyRowProps={() => ({
              sx: {
                '&:hover': {
                  backgroundColor: 'rgba(0,176,240,0.04)',
                  transition: 'all 0.3s ease'
                }
              }
            })}
            initialState={{
              sorting: [{ id: 'created_at', desc: true }]
            }}
          />
        )}
      </Paper>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Modifier la Tâche</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Nom"
              value={editForm.name}
              onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
              fullWidth
            />
            <TextField
              label="Description"
              value={editForm.description}
              onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
              fullWidth
              multiline
              rows={3}
            />
            <FormControl fullWidth>
              <InputLabel>Statut</InputLabel>
              <Select
                value={editForm.status}
                label="Statut"
                onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
              >
                <MenuItem value="CREATED">Créée</MenuItem>
                <MenuItem value="ASSIGNED">Assignée</MenuItem>
                <MenuItem value="RUNNING">En cours</MenuItem>
                <MenuItem value="PAUSED">En pause</MenuItem>
                <MenuItem value="COMPLETED">Terminée</MenuItem>
                <MenuItem value="FAILED">Échouée</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Progression (%)"
              type="number"
              value={editForm.progress}
              onChange={(e) => setEditForm({ ...editForm, progress: Number.parseInt(e.target.value) })}
              fullWidth
              inputProps={{ min: 0, max: 100 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Annuler</Button>
          <Button onClick={handleEditSubmit} variant="contained" color="primary">
            Enregistrer
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Confirmer la suppression</DialogTitle>
        <DialogContent>
          <Typography>
            Êtes-vous sûr de vouloir supprimer la tâche "{selectedTask?.name}" ?
          </Typography>
          <Alert severity="warning" sx={{ mt: 2 }}>
            Cette action est irréversible.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Annuler</Button>
          <Button onClick={handleDeleteConfirm} variant="contained" color="error">
            Supprimer
          </Button>
        </DialogActions>
      </Dialog>

      {/* Detail Dialog */}
      <Dialog open={detailDialogOpen} onClose={() => setDetailDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Détails de la Tâche</DialogTitle>
        <DialogContent dividers>
          {selectedTask && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Nom</Typography>
                <Typography variant="h6">{selectedTask.name}</Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Description</Typography>
                <Typography>{selectedTask.description || '-'}</Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Statut</Typography>
                <Chip
                  label={getStatusLabel(selectedTask.status)}
                  color={getStatusColor(selectedTask.status)}
                  size="small"
                />
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Progression</Typography>
                <Typography>{selectedTask.progress || 0}%</Typography>
              </Box>
              {selectedTask.command && (
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">Commande</Typography>
                  <Typography sx={{ fontFamily: 'monospace', fontSize: '0.875rem', backgroundColor: '#f5f5f5', p: 1, borderRadius: 1 }}>
                    {selectedTask.command}
                  </Typography>
                </Box>
              )}
              {selectedTask.assigned_to && (
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">Volontaire assigné</Typography>
                  <Typography>{selectedTask.assigned_to.name || '-'}</Typography>
                </Box>
              )}
              {selectedTask.dependencies && selectedTask.dependencies.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">Dépendances</Typography>
                  <Typography>{selectedTask.dependencies.length} tâche(s)</Typography>
                  <Button
                    size="small"
                    onClick={() => {
                      setDetailDialogOpen(false);
                      handleCheckDependencies(selectedTask);
                    }}
                  >
                    Voir les dépendances
                  </Button>
                </Box>
              )}
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Dates</Typography>
                <Typography variant="body2">
                  Créée: {selectedTask.created_at ? new Date(selectedTask.created_at).toLocaleString('fr-FR') : '-'}
                </Typography>
                {selectedTask.start_time && (
                  <Typography variant="body2">
                    Démarrée: {new Date(selectedTask.start_time).toLocaleString('fr-FR')}
                  </Typography>
                )}
                {selectedTask.end_time && (
                  <Typography variant="body2">
                    Terminée: {new Date(selectedTask.end_time).toLocaleString('fr-FR')}
                  </Typography>
                )}
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailDialogOpen(false)} variant="contained">Fermer</Button>
        </DialogActions>
      </Dialog>

      {/* Dependencies Dialog */}
      <Dialog open={dependenciesDialogOpen} onClose={() => setDependenciesDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Dépendances de la Tâche</DialogTitle>
        <DialogContent dividers>
          {dependencies && (
            <Box>
              {!dependencies.has_dependencies ? (
                <Alert severity="info">Cette tâche n'a pas de dépendances</Alert>
              ) : (
                <>
                  <Alert severity={dependencies.all_satisfied ? "success" : "warning"} sx={{ mb: 2 }}>
                    {dependencies.all_satisfied
                      ? "Toutes les dépendances sont satisfaites - La tâche peut démarrer"
                      : "Certaines dépendances ne sont pas encore satisfaites"}
                  </Alert>
                  <List>
                    {dependencies.dependencies.map((dep, index) => (
                      <ListItem
                        key={index}
                        secondaryAction={
                          dep.satisfied ? (
                            <CheckCircleIcon color="success" />
                          ) : (
                            <ErrorIcon color="error" />
                          )
                        }
                      >
                        <ListItemText
                          primary={dep.name}
                          secondary={`Statut: ${dep.status}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDependenciesDialogOpen(false)} variant="contained">Fermer</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
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

export default Tasks;
